'''
These functions are for use by other extensions for their reports.
'''
from datetime import datetime
import six
from six.moves import cStringIO as StringIO, zip
try:
    from collections import OrderedDict  # from python 2.7
except ImportError:
    from sqlalchemy.util import OrderedDict

import ckan.plugins as p
from ckan.plugins.toolkit import config
from ckan import model
from typing import Generator, Union, Dict, TypedDict, Optional
from sqlalchemy import func

Organization = TypedDict('Organization', {'id': str,
                                          'name': str,
                                          'title': str,
                                          'title_translated': Optional[Dict[str, str]]})


def all_organizations(include_none=False) -> Generator[Union[str, None], None, None]:
    '''Yields all the organization names, and also None if requested. Useful
    when assembling option_combinations'''
    if include_none:
        yield None
    organizations = model.Session.query(model.Group).\
        filter(model.Group.type == 'organization').\
        filter(model.Group.state == 'active').order_by('name')
    for organization in organizations:
        yield organization.name


def get_all_organizations(only_orgs_with_packages=False) -> Generator[Organization, None, None]:
    organizations = model.Session.query(model.Group.id, model.Group.name, model.Group.title,
                                        func.count(model.Package.id).label('package_count')).\
        filter(model.Group.type == 'organization').\
        filter(model.Group.state == 'active').\
        outerjoin(model.Package, model.Package.owner_org == model.Group.id).\
        group_by(model.Group.id).order_by(model.Group.title).all()

    for organization in organizations:
        extras = model.Session.query(model.GroupExtra.value.label('title_translated')).filter(
            model.GroupExtra.key == 'title_translated', model.GroupExtra.group_id == organization.id).first()
        title_translated: Dict[str,
                               str] = extras.title_translated if extras else {}
        org: Organization = {'id': organization.id,
                             'name': organization.name,
                             'title': organization.title,
                             'title_translated': title_translated}

        if only_orgs_with_packages:
            if organization.package_count > 0:
                yield (org)
        else:
            yield (org)


def go_down_tree(organization):
    '''Provided with an organization object, it walks down the hierarchy and yields
    each organization, including the one you supply.

    Essentially this is a slower version of Group.get_children_group_hierarchy
    because it returns Group objects, rather than dicts.
    '''
    yield organization
    for child in organization.get_children_groups(type='organization'):
        for grandchild in go_down_tree(child):
            yield grandchild


def filter_by_organizations(query, organization, include_sub_organizations):
    '''Given an SQLAlchemy ORM query object, it returns it filtered by the
    given organization and optionally its sub organizations too.
    '''
    if not organization:
        return query
    if isinstance(organization, six.string_types):
        organization = model.Group.get(organization)
        assert organization
    if include_sub_organizations:
        orgs = sorted([x for x in go_down_tree(organization)], key=lambda x: x.name)
        org_ids = [org.id for org in orgs]
        return query.filter(model.Package.owner_org.in_(org_ids))
    else:
        return query.filter(model.Package.owner_org == organization.id)


def dataset_notes(pkg):
    '''Returns a string with notes about the given package. It is
    configurable.'''
    expression = config.get('ckanext-report.notes.dataset')
    if not expression:
        return ''
    return eval(expression, None, {'pkg': pkg, 'asbool': p.toolkit.asbool})


def percent(numerator, denominator):
    if denominator == 0:
        return 100 if numerator else 0
    return int((numerator * 100.0) / denominator)


def make_csv_from_dicts(rows):
    import csv

    csvout = StringIO()
    csvwriter = csv.writer(
        csvout,
        dialect='excel',
        quoting=csv.QUOTE_NONNUMERIC
    )
    # extract the headers by looking at all the rows and
    # get a full list of the keys, retaining their ordering
    headers_ordered = []
    headers_set = set()
    for row in rows:
        new_headers = set(row.keys()) - headers_set
        headers_set |= new_headers
        for header in row.keys():
            if header in new_headers:
                headers_ordered.append(header)
    csvwriter.writerow(headers_ordered)
    for row in rows:
        items = []
        for header in headers_ordered:
            item = row.get(header, 'no record')
            if isinstance(item, datetime):
                item = item.strftime('%Y-%m-%d %H:%M')
            elif isinstance(item, (int, float, list, tuple)):
                item = six.text_type(item)
            elif item is None:
                item = ''
            else:
                item = str(item)
            items.append(item)
        try:
            csvwriter.writerow(items)
        except Exception as e:
            raise Exception('%s: %s, %s' % (e, row, items))
    csvout.seek(0)
    return csvout.read()


def ensure_data_is_dicts(data):
    '''Ensure that the data is a list of dicts, rather than a list of tuples
    with column names, as sometimes is the case. Changes it in place'''
    if data['table'] and isinstance(data['table'][0], (list, tuple)):
        new_data = []
        columns = data['columns']
        for row in data['table']:
            new_data.append(OrderedDict(zip(columns, row)))
        data['table'] = new_data
        del data['columns']


def anonymise_user_names(data, organization=None):
    '''Ensure any columns with names in are anonymised, unless the current user
    has privileges.

    NB this is only enabled for data.gov.uk - it is custom functionality.
    '''
    try:
        import ckanext.dgu.lib.helpers as dguhelpers
    except ImportError:
        # If this is not DGU then cannot do the anonymization
        return
    column_names = data['table'][0].keys() if data['table'] else []
    for col in column_names:
        if col.lower() in ('user', 'username', 'user name', 'author'):
            for row in data['table']:
                row[col] = dguhelpers.user_link_info(
                    row[col], organization=organization)[0]
