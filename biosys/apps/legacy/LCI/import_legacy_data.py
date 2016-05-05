"""
Usage with django-extensions runscript command: ./manage.py runscript legacy.LCI.import_legacy_data
"""

from __future__ import unicode_literals, print_function

import logging
import re

from openpyxl import load_workbook

from django.db.models.query import Q

from main.models import *
from main.utils import get_field
from upload.utils_openpyxl import TableData, is_blank_value
from upload.validation import to_integer_raise, to_float_raise, to_model_choice, \
    to_lookup_raise, to_string, to_date_raise, to_species_observation_raise, to_boolean_raise
from vegetation.models import *
from animals.models import *

logger = logging.getLogger('import_lci')

DATA_FILE = 'LCI_NC_MonSiteData_15Jan2016.xlsx'
# some global variables
current_ws = None
row_count = None


def build_model_arguments(row_data, mapping):
    """
    mapping = {
        'Project': {
            'field': 'project',
            'map': lambda x: str(x),
            'primary': True, if True the field is used a a lookup field when updating a record instead of creating a new
             one
        },
        'Parent Site': {
            'field': 'parent_site',
            'map': None
        },
    :param row_data:
    :param mapping:
    :return:
    """
    kwargs = {}
    defaults = {}
    errors = []
    for col_name, map_desc in mapping.iteritems():
        col_value = row_data.get(col_name, None)
        field = map_desc.get('field', None)
        if field:
            try:
                map_func = map_desc.get('map', None)
                field_value = map_func(col_value, row_data) if callable(map_func) else col_value
                if map_desc.get('primary', False):
                    kwargs[field] = field_value
                else:
                    defaults[field] = field_value
            except Exception as e:
                msg = "Col: '{}' Value '{}': {}".format(col_name, col_value, e)
                # logger.warning(msg)
                errors.append(msg)
    return kwargs, defaults, errors


def update_or_create_model(model, row_data, mapping):
    kwargs, defaults, errors = build_model_arguments(row_data, mapping)
    if not errors:
        obj, created = model.objects.update_or_create(defaults=defaults, **kwargs)
        return obj, created, errors
    else:
        raise Exception(*errors)


def create_model(model, row_data, mapping):
    kwargs, defaults, errors = build_model_arguments(row_data, mapping)
    if not errors:
        created = True
        obj = model.objects.create(**defaults)
        return obj, created, errors
    else:
        raise Exception(*errors)


def update_or_create_project(row_data):
    model = Project
    mapping = {
        'Project': {
            'field': 'title',
            'primary': True,
        },
        'Datum': {
            'field': 'datum',
            'map': lambda x, r: to_model_choice(DATUM_CHOICES, x) if x else None
        }
    }
    return update_or_create_model(model, row_data, mapping)


def only_digit(x):
    return re.sub('[^0-9\.]', '', str(x))


def update_or_create_site(project, row_data):
    model = Site
    mapping = {
        'Project': {
            'field': 'project',
            'map': lambda x, r: project,
        },
        'Parent Site': {
            'field': 'parent_site',
            'map': lambda x, r: model.objects.get_or_create(project=project, site_code=x)[0]
        },
        'Site Code': {
            'field': 'site_code',
            'primary': True,
            'map': None
        },
        'Site Name': {
            'field': 'site_name',
            'map': None
        },
        'Date established': {
            'field': 'date_established'
        },
        'Datum': {
            'field': 'datum',
            'map': lambda x, r: to_model_choice(DATUM_CHOICES, x) if x else None
        },
        'Latitude': {
            'field': 'latitude',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'Longitude': {
            'field': 'longitude',
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'Accuracy': {
            'field': 'accuracy',
            # turn '50m' into 50.0
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'Collector': {
            'field': 'established_by',
            'map': lambda v, r: to_string(v)
        },
        'Bearing (degree)': {
            'field': 'bearing',
            'map': lambda v, r: to_float_raise(v)
        },
        'Width': {
            'field': 'width',
            'map': lambda v, r: only_digit(v)
        },
        'Hight': {
            'field': 'height',
            'map': lambda v, r: only_digit(v)
        },
        'Aspect': {
            'field': 'aspect',
            'map': lambda x, r: to_model_choice(Site.ASPECT_CHOICES, x) if x else None
        },
        'Slope (degree)': {
            'field': 'slope',
            'map': lambda x, r: to_integer_raise(only_digit(x), None)
        },
        'Altitude': {
            'field': 'altitude',
            'map': lambda x, r: to_float_raise(only_digit(x), None)
        },
        'Location': {
            'field': 'location',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'location'), x)
        },
        'Geology Group': {
            'field': 'geology_group',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'geology_group'), x)
        },
        'Vegetation Group': {
            'field': 'vegetation_group',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'vegetation_group'), x)
        },
        'Tenure': {
            'field': 'tenure',
            'map': lambda v, r: to_string(v)
        },
        'Underlaying geology ': {
            'field': 'underlaying_geology',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'underlaying_geology'), x)
        },
        'Distance to closest water (m)': {
            'field': 'closest_water_distance',
            'map': lambda x, r: to_integer_raise(only_digit(x), None)
        },
        'Type of closest water': {
            'field': 'closest_water_type',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'closest_water_type'), x)
        },
        'Landform pattern (300m radius)': {
            'field': 'landform_pattern',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'landform_pattern'), x)
        },
        'Landform element (20m radius)': {
            'field': 'landform_element',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'landform_element'), x)
        },
        'Soil surface texture': {
            'field': 'soil_surface_texture',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'soil_surface_texture'), x)
        },
        'Soil colour': {
            'field': 'soil_colour',
            'map': lambda v, r: to_string(v)
        },
        'Photos taken': {
            'field': 'photos_taken',
            'map': lambda v, r: to_string(v)
        },
        'Historical Information': {
            'field': 'historical_info',
            'map': lambda v, r: to_string(v)
        },
        'Comments': {
            'field': 'comments',
            'map': lambda v, r: to_string(v)
        },
    }
    return update_or_create_model(model, row_data, mapping)


def load_sites(ws):
    global row_count
    table_reader = TableData(ws)
    row_count = 2
    for row in list(table_reader.rows_by_col_header_it()):
        try:
            project, created, errors = update_or_create_project(row)
            if errors:
                logger.warning('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
            else:
                site, created, errors = update_or_create_site(project, row)
                if errors:
                    logger.warning('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.exception('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def update_or_create_visit(project, site, row_data):
    model = Visit
    mapping = {
        'Project': {
            'field': 'project',
            'map': lambda x, r: project,
        },
        'Visit Name': {
            'field': 'name',
            'map': lambda v, r: to_string(v),
            'primary': True,
        },
        'Start Date': {
            'field': 'start_date',
            'map': lambda v, r: to_date_raise(v),
        },
        'End Date': {
            'field': 'end_date',
            'map': lambda v, r: to_date_raise(v),
        },
        'Trap Nights': {
            'field': 'trap_nights',
            'map': lambda v, r: to_integer_raise(only_digit(v)),
        },
        'Comments': {
            'field': 'comments',
            'map': lambda v, r: to_string(v)
        },
    }
    visit, created, errors = update_or_create_model(model, row_data, mapping)
    # add the site to this visit
    if not errors:
        visit.sites.add(site)
        visit.save()
    return site, created, errors


def load_visits(ws):
    global row_count
    table_reader = TableData(ws)
    row_count = 2
    for row_data in list(table_reader.rows_by_col_header_it()):
        try:
            project_title = row_data.get('Project', None)
            project = Project.objects.get(title=project_title)
            site_code = row_data.get('Sites', None)
            site = Site.objects.get(site_code=site_code)
            visit, created, errors = update_or_create_visit(project, site, row_data)
            if errors:
                logger.warning('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.exception('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def update_or_create_site_visit(row_data):
    model = SiteVisit

    mapping = {
        'Visit Name': {
            'field': 'visit',
            'map': lambda v, r: Visit.objects.get(name=v),
            'primary': True,
        },
        'Site Code': {
            'field': 'site',
            'map': lambda v, r: Site.objects.get(site_code=v),
            'primary': True,
        },
    }
    return update_or_create_model(model, row_data, mapping)


def update_or_create_site_characteristic(row_data):
    model = SiteCharacteristic
    mapping = {
        'Visit Name': {
            'field': 'site_visit',
            'map': lambda v, r: update_or_create_site_visit(r)[0],
            'primary': True,
        },
        'Underlaying geology': {
            'field': 'underlaying_geology',
            'map': lambda x, r: to_lookup_raise(get_field(model, 'underlaying_geology'), x)
        },
        'Distance to closest water (m)': {
            'field': 'closest_water_distance',
            'map': lambda x, r: to_integer_raise(only_digit(x), None)
        },
        'Type of closest water': {
            'field': 'closest_water_type',
            'map': lambda x, r: to_lookup_raise(get_field(model, 'closest_water_type'), x)
        },
        'Landform pattern (300m radius)': {
            'field': 'landform_pattern',
            'map': lambda x, r: to_lookup_raise(get_field(model, 'landform_pattern'), x)
        },
        'Landform element (20m radius)': {
            'field': 'landform_element',
            'map': lambda x, r: to_lookup_raise(get_field(model, 'landform_element'), x)
        },
        'Soil surface texture': {
            'field': 'soil_surface_texture',
            'map': lambda x, r: to_lookup_raise(get_field(model, 'soil_surface_texture'), x)
        },
        'Soil colour': {
            'field': 'soil_colour',
            'map': lambda v, r: to_string(v)
        },
        'Comments': {
            'field': 'comments',
            'map': lambda v, r: to_string(v)
        },
    }
    kwargs, defaults, errors = build_model_arguments(row_data, mapping)
    obj, created = model.objects.update_or_create(defaults=defaults, **kwargs)
    return obj, created, errors


def load_site_characteristics(ws):
    global row_count
    table_reader = TableData(ws)
    row_count = 2
    for row_data in list(table_reader.rows_by_col_header_it()):
        try:
            obj, created, errors = update_or_create_site_characteristic(row_data)
            if errors:
                logger.warning('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.exception('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def update_or_create_vegetation_visit(row_data):
    model = VegetationVisit
    mapping = {
        'Site Code': {
            'field': 'site_visit',
            'map': lambda v, r: update_or_create_site_visit(r)[0],
            'primary': True,
        },
        'Vegetation Collector': {
            'field': 'collector',
            'map': lambda v, r: to_string(v),
        },
        'Visit Date': {
            'field': 'date',
            'map': lambda v, r: to_date_raise(v),
        },
    }
    return update_or_create_model(model, row_data, mapping)


def get_or_create_species_observation(species, site_visit, row_data):
    query = Q(input_name=species)
    if site_visit is not None:
        query &= Q(site_visit=site_visit)
    sp_obs = SpeciesObservation.objects.filter(query).first()
    data = {
        'Species validation status': row_data.get('Species Validation', ''),
        'Species uncertainty': row_data.get('Species Uncertainty', '')
    }
    if sp_obs is None:
        try:
            sp_obs = to_species_observation_raise(species, site_visit=site_visit, row_data=data)
        except Exception as e:
            # probably didn't validate
            logger.warning('{} Row# {}: {}'.format(current_ws, row_count, e))
            data = {
                'Species validation status': 'do not validate',
            }
            sp_obs = to_species_observation_raise(species, site_visit=site_visit, row_data=data)
    return sp_obs


def update_or_create_stratum_species(row_data):
    model = StratumSpecies
    vegetation_visit = update_or_create_vegetation_visit(row_data)[0]
    mapping = {
        'Site Code': {
            'field': 'vegetation_visit',
            'map': lambda v, r: vegetation_visit,
            'primary': True,
        },
        'Significance': {
            'field': 'significance',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'significance'), v),
        },
        'Stratum': {
            'field': 'stratum',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'stratum'), v),
            'primary': True
        },
        'Species': {
            'field': 'species',
            'map': lambda v, r: get_or_create_species_observation(v, vegetation_visit.site_visit, r),
            'primary': True
        },
        'Collector No': {
            'field': 'collector_no',
            'map': lambda v, r: to_string(v),
        },
        'Average Height (m)': {
            'field': 'avg_height',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'Cover    %': {
            'field': 'cover',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'Basal Area': {
            'field': 'basal_area',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'Bitterlich % cover': {
            'field': 'bitterlich_cover',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'Juvenile <2m': {
            'field': 'juv_lt_2m',
            'map': lambda v, r: to_boolean_raise(v),
        },
        'Juvenile >2m': {
            'field': 'juv_mt_2m',
            'map': lambda v, r: to_boolean_raise(v),
        },
        'Adult': {
            'field': 'adult',
            'map': lambda v, r: to_boolean_raise(v),
        },
        'Mature (at peak of prod.)': {
            'field': 'mature',
            'map': lambda v, r: to_boolean_raise(v),
        },
        'Condition': {
            'field': 'condition',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'condition'), v),
        },
        'flowering': {
            'field': 'flowering',
            'map': lambda v, r: to_boolean_raise(v),
        },
        'fruiting': {
            'field': 'fruiting',
            'map': lambda v, r: to_boolean_raise(v),
        },
        'seeding': {
            'field': 'seeding',
            'map': lambda v, r: to_boolean_raise(v),
        },
        'Comments': {
            'field': 'comments',
            'map': lambda v, r: to_string(v)
        },
    }
    return update_or_create_model(model, row_data, mapping)


def load_stratum_species(ws):
    global row_count
    table_reader = TableData(ws)
    row_count = 2
    for row_data in list(table_reader.rows_by_col_header_it()):
        try:
            # get site visit
            obj, created, errors = update_or_create_stratum_species(row_data)
            if errors:
                logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.error('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def update_or_create_ground_cover_summary(vegetation_visit, row_data):
    model = GroundCoverSummary
    mapping = {
        'A': {
            'field': 'vegetation_visit',
            'map': lambda v, r: vegetation_visit,
            'primary': True
        },
        'E': {
            'field': 'perennial_grass',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'F': {
            'field': 'annual_grass',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'G': {
            'field': 'herb',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'H': {
            'field': 'litter',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'I': {
            'field': 'logs',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'J': {
            'field': 'rock_gravel',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'K': {
            'field': 'bare_ground',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'L': {
            'field': 'termite_mound',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'N': {
            'field': 'comments',
            'map': lambda v, r: to_string(v),
        },
    }
    return update_or_create_model(model, row_data, mapping)


def update_or_create_transect_observation(vegetation_visit, row_data):
    model = TransectObservation
    mapping = {
        'A': {
            'field': 'vegetation_visit',
            'map': lambda v, r: vegetation_visit,
            'primary': True
        },
        'O': {
            'field': 'perennial_grass',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'P': {
            'field': 'annual_grass',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'Q': {
            'field': 'herb',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'R': {
            'field': 'litter',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'S': {
            'field': 'logs',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'T': {
            'field': 'rock_gravel',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'U': {
            'field': 'bare_ground',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'V': {
            'field': 'termite_mound',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'W': {
            'field': 'low_shrub',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'X': {
            'field': 'shrub',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'Y': {
            'field': 'tree',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
    }
    return update_or_create_model(model, row_data, mapping)


def create_transect_distinct_change(vegetation_visit, data):
    model = TransectDistinctChanges
    mapping = {
        'Vegetation Visit': {
            'field': 'vegetation_visit',
            'map': lambda v, r: vegetation_visit,
        },
        'Point of Change': {
            'field': 'point_of_change',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'Change From': {
            'field': 'change_from',
            'map': lambda v, r: to_string(v),
        },
        'Change To': {
            'field': 'change_to',
            'map': lambda v, r: to_string(v),
        },
    }
    return create_model(model, data, mapping)


def update_or_create_basal_bitterlich_observation(vegetation_visit, row_data):
    model = BasalBitterlichObservation
    mapping = {
        'A': {
            'field': 'vegetation_visit',
            'map': lambda v, r: vegetation_visit,
            'primary': True
        },
        'AI': {
            'field': 'basal_area',
            'map': lambda v, r: to_integer_raise(only_digit(v)),
        },
        'AJ': {
            'field': 'bitterlich_trees',
            'map': lambda v, r: to_integer_raise(only_digit(v)),
        },
        'AK': {
            'field': 'bitterlich_shrubs',
            'map': lambda v, r: to_integer_raise(only_digit(v)),
        },
    }
    return update_or_create_model(model, row_data, mapping)


def update_or_create_erosion_peg(vegetation_visit, data):
    model = ErosionPeg
    mapping = {
        'vegetation_visit': {
            'field': 'vegetation_visit',
            'map': lambda v, r: vegetation_visit,
            'primary': True
        },
        'peg_ID': {
            'field': 'peg_ID',
            'map': lambda v, r: to_string(v),
            'primary': True
        },
        'transect_x': {
            'field': 'transect_x',
            'map': lambda v, r: to_float_raise(only_digit(v), 0),
        },
        'transect_y': {
            'field': 'transect_y',
            'map': lambda v, r: to_float_raise(only_digit(v), 0),
        },
        'y_direction': {
            'field': 'y_direction',
            'map': lambda v, r: to_model_choice(ErosionPeg.Y_DIRECTION_CHOICES, to_string(v)),
        },
    }
    return update_or_create_model(model, data, mapping)


def update_or_create_peg_observation(vegetation_visit, data):
    model = PegObservation
    mapping = {
        'vegetation_visit': {
            'field': 'vegetation_visit',
            'map': lambda v, r: vegetation_visit,
            'primary': True
        },
        'peg_ID': {
            'field': 'peg_ID',
            'map': lambda v, r: to_string(v),
            'primary': True
        },
        'intact_litter': {
            'field': 'intact_litter',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'frag_decay': {
            'field': 'frag_decay',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'crust': {
            'field': 'crust',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'worm': {
            'field': 'worm',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'organic': {
            'field': 'organic',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'erosion': {
            'field': 'erosion',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'comments': {
            'field': 'comments',
            'map': lambda v, r: to_string(v),
        },
    }
    return update_or_create_model(model, data, mapping)


def load_vegetation(ws):
    global row_count
    table_reader = TableData(ws)
    row_count = 2
    # don't work with the column header her, too many columns with same name
    for row_data in list(table_reader.rows_by_col_letter_it()):
        try:
            # get site visit
            vegetation_visit_data = {
                'Visit Name': row_data.get('A'),
                'Site Code': row_data.get('B'),
                'Vegetation Collector': row_data.get('C'),
                'Visit Date': row_data.get('D'),
            }
            vegetation_visit, created, errors = update_or_create_vegetation_visit(vegetation_visit_data)
            if not errors:
                obj, created, errors = update_or_create_ground_cover_summary(vegetation_visit, row_data)
                if errors:
                    logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
                obj, created, errors = update_or_create_transect_observation(vegetation_visit, row_data)
                if errors:
                    logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))

                # 3 TransectDistinctChanges
                # delete previous
                TransectDistinctChanges.objects.filter(vegetation_visit=vegetation_visit).delete()
                if not is_blank_value(row_data.get('Z')):
                    data = {
                        'Vegetation Visit': vegetation_visit,
                        'Point of Change': row_data.get('Z'),
                        'Change From': row_data.get('AA'),
                        'Change To': row_data.get('AB'),
                    }
                    obj, created, errors = create_transect_distinct_change(vegetation_visit, data)
                    if errors:
                        logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))

                if not is_blank_value(row_data.get('AC')):
                    data = {
                        'Vegetation Visit': vegetation_visit,
                        'Point of Change': row_data.get('AC'),
                        'Change From': row_data.get('AD'),
                        'Change To': row_data.get('AE'),
                    }
                    obj, created, errors = create_transect_distinct_change(vegetation_visit, data)
                    if errors:
                        logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))

                if not is_blank_value(row_data.get('AF')):
                    data = {
                        'Vegetation Visit': vegetation_visit,
                        'Point of Change': row_data.get('AF'),
                        'Change From': row_data.get('AG'),
                        'Change To': row_data.get('AH'),
                    }
                    obj, created, errors = create_transect_distinct_change(vegetation_visit, data)
                    if errors:
                        logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))

                # BasalBitterlichObservation
                obj, created, errors = update_or_create_basal_bitterlich_observation(vegetation_visit, row_data)
                if errors:
                    logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))

                # ErosionPegs
                if not is_blank_value(row_data.get('AM')):
                    peg_id = row_data.get('AL')
                    if is_blank_value(peg_id):
                        peg_id = 'A'
                    data = {
                        'vegetation_visit': vegetation_visit,
                        'peg_ID': peg_id,
                        'transect_x': row_data.get('AM'),
                        'transect_y': row_data.get('AN'),
                        'y_direction': row_data.get('AO'),
                    }
                    obj, created, errors = update_or_create_erosion_peg(vegetation_visit, data)
                    if errors:
                        logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))

                if not is_blank_value(row_data.get('AQ')):
                    peg_id = row_data.get('AP')
                    if is_blank_value(peg_id):
                        peg_id = 'B'
                    data = {
                        'vegetation_visit': vegetation_visit,
                        'peg_ID': peg_id,
                        'transect_x': row_data.get('AQ'),
                        'transect_y': row_data.get('AR'),
                        'y_direction': row_data.get('AS'),
                    }
                    obj, created, errors = update_or_create_erosion_peg(vegetation_visit, data)
                    if errors:
                        logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))

                if not is_blank_value(row_data.get('AU')):
                    peg_id = row_data.get('AT')
                    if is_blank_value(peg_id):
                        peg_id = 'C'
                    data = {
                        'vegetation_visit': vegetation_visit,
                        'peg_ID': peg_id,
                        'transect_x': row_data.get('AU', 0),
                        'transect_y': row_data.get('AV', 0),
                        'y_direction': row_data.get('AW'),
                    }
                    obj, created, errors = update_or_create_erosion_peg(vegetation_visit, data)
                    if errors:
                        logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))

                # 3 PegObservations
                comments = row_data.get('BS')
                peg_id = row_data.get('AX')
                if not is_blank_value(peg_id):
                    data = {
                        'vegetation_visit': vegetation_visit,
                        'peg_ID': peg_id,
                        'intact_litter': row_data.get('AY'),
                        'frag_decay': row_data.get('AZ'),
                        'crust': row_data.get('BA'),
                        'worm': row_data.get('BB'),
                        'organic': row_data.get('BC'),
                        'erosion': row_data.get('BD'),
                        'comments': comments,
                    }
                    obj, created, errors = update_or_create_peg_observation(vegetation_visit, data)
                    if errors:
                        logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))

                peg_id = row_data.get('BE')
                if not is_blank_value(peg_id):
                    data = {
                        'vegetation_visit': vegetation_visit,
                        'peg_ID': peg_id,
                        'intact_litter': row_data.get('BF'),
                        'frag_decay': row_data.get('BG'),
                        'crust': row_data.get('BH'),
                        'worm': row_data.get('BI'),
                        'organic': row_data.get('BJ'),
                        'erosion': row_data.get('BK'),
                        'comments': comments,
                    }
                    obj, created, errors = update_or_create_peg_observation(vegetation_visit, data)
                    if errors:
                        logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))

                peg_id = row_data.get('BL')
                if not is_blank_value(peg_id):
                    data = {
                        'vegetation_visit': vegetation_visit,
                        'peg_ID': peg_id,
                        'intact_litter': row_data.get('BM'),
                        'frag_decay': row_data.get('BN'),
                        'crust': row_data.get('BO'),
                        'worm': row_data.get('BP'),
                        'organic': row_data.get('BQ'),
                        'erosion': row_data.get('BR'),
                        'comments': comments,
                    }
                    obj, created, errors = update_or_create_peg_observation(vegetation_visit, data)
                    if errors:
                        logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
            else:
                logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))

        except Exception as e:
            logger.error('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def load_stratum_summary(ws):
    global row_count
    table_reader = TableData(ws)
    row_count = 2
    # don't work with the column header her, too many columns with same name
    for row_data in list(table_reader.rows_by_col_letter_it()):
        try:
            # get site visit
            vegetation_visit_data = {
                'Visit Name': row_data.get('A'),
                'Site Code': row_data.get('B'),
                'Vegetation Collector': row_data.get('C'),
                'Visit Date': row_data.get('D'),
            }
            vegetation_visit, created, errors = update_or_create_vegetation_visit(vegetation_visit_data)
            if not errors:
                obj, created, errors = update_or_create_stratum_summary(vegetation_visit, row_data)
                if errors:
                    logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
            else:
                logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.error('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def update_or_create_stratum_summary(vegetation_visit, row_data):
    # expect row_data to be by col_letter
    model = StratumSummary
    mapping = {
        'A': {
            'field': 'vegetation_visit',
            'map': lambda v, r: vegetation_visit,
            'primary': True
        },
        'E': {
            'field': 'stratum',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'stratum'), v),
            'primary': True
        },
        'F': {
            'field': 'growth_form',
            'map': lambda v, r: to_string(v),
        },
        'G': {
            'field': 'crown_cover',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'H': {
            'field': 'avg_height',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'I': {
            'field': 'max_height',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
    }
    return update_or_create_model(model, row_data, mapping)


def load_disturbance_indicators(ws):
    global row_count
    table_reader = TableData(ws)
    row_count = 2
    # don't work with the column header her, too many columns with same name
    for row_data in list(table_reader.rows_by_col_letter_it()):
        try:
            # get site visit
            vegetation_visit_data = {
                'Visit Name': row_data.get('A'),
                'Site Code': row_data.get('B'),
                'Vegetation Collector': row_data.get('C'),
                'Visit Date': row_data.get('D'),
            }
            vegetation_visit, created, errors = update_or_create_vegetation_visit(vegetation_visit_data)
            if not errors:
                obj, created, errors = update_or_create_disturbance_indicator(vegetation_visit, row_data)
                if errors:
                    logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
            else:
                logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.error('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def update_or_create_disturbance_indicator(vegetation_visit, row_data):
    # expect row_data to be by col_letter
    model = DisturbanceIndicator
    mapping = {
        'A': {
            'field': 'vegetation_visit',
            'map': lambda v, r: vegetation_visit,
            'primary': True
        },
        'E': {
            'field': 'evidence_recent_fire',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'evidence_recent_fire'), v),
            'primary': True
        },
        'F': {
            'field': 'fire_intensity',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'fire_intensity'), v),
        },
        'G': {
            'field': 'recently_burned_percent',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'H': {
            'field': 'scorch_height',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'I': {
            'field': 'cattle_sighted',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'cattle_sighted'), v),
        },
        'J': {
            'field': 'grazing_level',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'grazing_level'), v),
        },
        'K': {
            'field': 'tracks_trampling',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'tracks_trampling'), v),
        },
        'L': {
            'field': 'cattle_dung',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'cattle_dung'), v),
        },
        'M': {
            'field': 'signs_damage_percent',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'N': {
            'field': 'pigs',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'pigs'), v),
        },
        'O': {
            'field': 'cats',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'cats'), v),
        },
        'P': {
            'field': 'horses_donkeys',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'horses_donkeys'), v),
        },
        'Q': {
            'field': 'camels',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'camels'), v),
        },
        'R': {
            'field': 'weed_percent',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'S': {
            'field': 'comments',
            'map': lambda v, r: to_string(v),
        },
    }
    return update_or_create_model(model, row_data, mapping)


def load_plant_observation(ws):
    global row_count
    table_reader = TableData(ws)
    row_count = 2
    # don't work with the column header her, too many columns with same name
    for row_data in list(table_reader.rows_by_col_letter_it()):
        try:
            # get site visit
            vegetation_visit_data = {
                'Visit Name': row_data.get('A'),
                'Site Code': row_data.get('B'),
                'Vegetation Collector': row_data.get('C'),
                'Visit Date': row_data.get('D'),
            }
            vegetation_visit, created, errors = update_or_create_vegetation_visit(vegetation_visit_data)
            if not errors:
                obj, created, errors = update_or_create_plant_observation(vegetation_visit, row_data)
                if errors:
                    logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
            else:
                logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.error('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def update_or_create_plant_observation(vegetation_visit, row_data):
    # expect row_data to be by col_letter
    model = PlantObservation
    mapping = {
        'A': {
            'field': 'vegetation_visit',
            'map': lambda v, r: vegetation_visit,
            'primary': True
        },
        'E': {
            'field': 'species',
            'map': lambda v, r: get_or_create_species_observation(v, vegetation_visit.site_visit, r),
            'primary': True
        },
        'F': {
            'field': 'introduced',
            'map': lambda v, r: to_boolean_raise(v),
        },
        'G': {
            'field': 'extent',
            'map': lambda v, r: to_string(v),
        },
        'H': {
            'field': 'density',
            'map': lambda v, r: to_string(v),
        },
        'I': {
            'field': 'invasiveness',
            'map': lambda v, r: to_string(v),
        },
    }
    return update_or_create_model(model, row_data, mapping)


def load_bio_indicator(ws):
    global row_count
    table_reader = TableData(ws)
    row_count = 2
    # don't work with the column header her, too many columns with same name
    for row_data in list(table_reader.rows_by_col_letter_it()):
        try:
            # get site visit
            vegetation_visit_data = {
                'Visit Name': row_data.get('A'),
                'Site Code': row_data.get('B'),
                'Vegetation Collector': row_data.get('C'),
                'Visit Date': row_data.get('D'),
            }
            vegetation_visit, created, errors = update_or_create_vegetation_visit(vegetation_visit_data)
            if not errors:
                obj, created, errors = update_or_create_bio_indicator(vegetation_visit, row_data)
                if errors:
                    logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
            else:
                logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.error('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def update_or_create_bio_indicator(vegetation_visit, row_data):
    # expect row_data to be by col_letter
    model = BiodiversityIndicator
    mapping = {
        'A': {
            'field': 'vegetation_visit',
            'map': lambda v, r: vegetation_visit,
            'primary': True
        },
        'E': {
            'field': 'fauna_habitat',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'fauna_habitat'), v),
        },
        'F': {
            'field': 'veg_cover',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'veg_cover'), v),
        },
        'G': {
            'field': 'crevices',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'crevices'), v),
        },
        'H': {
            'field': 'tree_hollows',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'tree_hollows'), v),
        },
        'I': {
            'field': 'logs',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'logs'), v),
        },
        'J': {
            'field': 'food_avail',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'food_avail'), v),
        },
        'K': {
            'field': 'fruiting',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'fruiting'), v),
        },
        'L': {
            'field': 'flowering',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'flowering'), v),
        },
        'M': {
            'field': 'seeding',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'seeding'), v),
        },
        'N': {
            'field': 'termites',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'termites'), v),
        },
        'O': {
            'field': 'traces',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'traces'), v),
        },
        'P': {
            'field': 'sightings',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'sightings'), v),
        },
        'Q': {
            'field': 'tracks',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'tracks'), v),
        },
        'R': {
            'field': 'scats',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'scats'), v),
        },
        'S': {
            'field': 'others',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'others'), v),
        },
        'T': {
            'field': 'comments',
            'map': lambda v, r: to_string(v),
        },
    }
    return update_or_create_model(model, row_data, mapping)


def load_trap(ws):
    model = Trap
    global row_count
    table_reader = TableData(ws)
    row_count = 2
    site_visit_pks = []
    for row_data in list(table_reader.rows_by_col_letter_it()):
        try:
            # get site visit
            site_visit_data = {
                'Visit Name': row_data.get('A'),
                'Site Code': row_data.get('B'),
            }
            site_visit, created, errors = update_or_create_site_visit(site_visit_data)
            if not errors:
                # delete all records
                if site_visit.pk not in site_visit_pks:
                    model.objects.filter(site_visit=site_visit).delete()
                    site_visit_pks.append(site_visit.pk)
                obj, created, errors = create_trap(site_visit, row_data)
                if errors:
                    logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
            else:
                logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.error('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def create_trap(site_visit, row_data):
    # expect row_data to be by col_letter
    model = Trap
    mapping = {
        'A': {
            'field': 'site_visit',
            'map': lambda v, r: site_visit,
        },
        'C': {
            'field': 'trapline_ID',
            'map': lambda v, r: to_string(v),
        },
        'D': {
            'field': 'trap_type',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'trap_type'), v),
        },
        'E': {
            'field': 'open_date',
            'map': lambda v, r: to_date_raise(v),
        },
        'F': {
            'field': 'close_date',
            'map': lambda v, r: to_date_raise(v),
        },
        'G': {
            'field': 'datum',
            'map': lambda x, r: to_model_choice(DATUM_CHOICES, x) if x else None
        },
        'H': {
            'field': 'start_latitude',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'I': {
            'field': 'start_longitude',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'J': {
            'field': 'stop_latitude',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'K': {
            'field': 'stop_longitude',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'L': {
            'field': 'accuracy',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'M': {
            'field': 'traps_number',
            'map': lambda v, r: to_integer_raise(only_digit(v)),
        },
        'N': {
            'field': 'comments',
            'map': lambda v, r: to_string(v),
        },
    }
    return create_model(model, row_data, mapping)


def load_animal_observations(ws):
    model = AnimalObservation
    global row_count
    table_reader = TableData(ws)
    row_count = 2
    site_visit_pks = []
    for row_data in list(table_reader.rows_by_col_letter_it()):
        try:
            # get site visit
            site_visit_data = {
                'Visit Name': row_data.get('A'),
                'Site Code': row_data.get('B'),
            }
            site_visit, created, errors = update_or_create_site_visit(site_visit_data)
            if not errors:
                # delete all records
                if site_visit.pk not in site_visit_pks:
                    model.objects.filter(site_visit=site_visit).delete()
                    site_visit_pks.append(site_visit.pk)
                obj, created, errors = create_animal_observation(site_visit, row_data)
                if errors:
                    logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
            else:
                logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.error('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def create_animal_observation(site_visit, row_data):
    # expect row_data to be by col_letter
    model = AnimalObservation
    mapping = {
        'A': {
            'field': 'site_visit',
            'map': lambda v, r: site_visit,
        },
        'C': {
            'field': 'collector',
            'map': lambda v, r: to_string(v),
        },
        'D': {
            'field': 'date',
            'map': lambda v, r: to_date_raise(v),
        },
        'E': {
            'field': 'trap_no',
            'map': lambda v, r: to_string(v),
        },
        'F': {
            'field': 'trap_type',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'trap_type'), v),
        },
        'G': {
            'field': 'capture_type',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'capture_type'), v),
        },
        'H': {
            'field': 'species',
            'map': lambda v, r: get_or_create_species_observation(v, site_visit, r),
        },
        'K': {
            'field': 'sex',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'sex'), v),
        },
        'L': {
            'field': 'microchip_id',
            'map': lambda v, r: to_string(v),
        },
        'M': {
            'field': 'tissue_number',
            'map': lambda v, r: to_string(v),
        },
        'N': {
            'field': 'tissue_type',
            'map': lambda v, r: to_string(v),
        },
        'O': {
            'field': 'fate',
            'map': lambda v, r: to_string(v),
        },
        'P': {
            'field': 'gross_weight',
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'Q': {
            'field': 'bag_weight',
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'R': {
            'field': 'net_weight',
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'S': {
            'field': 'age',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'age'), v),
        },
        'T': {
            'field': 'head_length',
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'U': {
            'field': 'pes_length',
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'V': {
            'field': 'reproductive_condition',
            'map': lambda v, r: to_string(v)
        },
        'W': {
            'field': 'pouch',
            'map': lambda v, r: to_string(v)
        },
        'X': {
            'field': 'test_length',
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'Y': {
            'field': 'test_width',
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'Z': {
            'field': 'svl',
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'AA': {
            'field': 'tail_length',
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'AB': {
            'field': 'tail_condition',
            'map': lambda v, r: to_string(v)
        },
        'AC': {
            'field': 'comments',
            'map': lambda v, r: to_string(v)
        },
    }
    return create_model(model, row_data, mapping)


def load_opportunistic_observations(ws):
    global row_count
    table_reader = TableData(ws)
    row_count = 2
    for row_data in list(table_reader.rows_by_col_header_it()):
        try:
            obj, created, errors = create_opportunistic_observation(row_data)
            if errors:
                logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.error('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def create_opportunistic_observation(row_data):
    model = OpportunisticObservation
    mapping = {
        'Date': {
            'field': 'date',
            'map': lambda v, r: to_date_raise(v)
        },
        'Observer': {
            'field': 'observer',
            'map': lambda v, r: to_string(v)
        },
        'Species': {
            'field': 'species',
            'map': lambda v, r: get_or_create_species_observation(v, None, r)
        },
        'Location': {
            'field': 'location',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'location'), v)
        },
        'Observation Type': {
            'field': 'observation_type',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'observation_type'), v)
        },
        'Datum': {
            'field': 'datum',
            'map': lambda x, r: to_model_choice(DATUM_CHOICES, x) if x else None
        },
        'Latitude': {
            'field': 'latitude',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'Longitude': {
            'field': 'longitude',
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'Accuracy': {
            'field': 'accuracy',
            # turn '50m' into 50.0
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'Comments': {
            'field': 'comments',
            'map': lambda v, r: to_string(v)
        }
    }
    return create_model(model, row_data, mapping)


def load_birds_observations(ws):
    global row_count
    table_reader = TableData(ws)
    row_count = 2
    for row_data in list(table_reader.rows_by_col_header_it()):
        try:
            obj, created, errors = create_bird_observation(row_data)
            if errors:
                logger.error('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.error('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def create_bird_observation(row_data):
    model = OpportunisticObservation
    mapping = {
        'Date': {
            'field': 'date',
            'map': lambda v, r: to_date_raise(v)
        },
        'Collector': {
            'field': 'observer',
            'map': lambda v, r: to_string(v)
        },
        'Species': {
            'field': 'species',
            'map': lambda v, r: get_or_create_species_observation(v, None, r)
        },
        'Location': {
            'field': 'location',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'location'), v)
        },
        'Veg': {  # use this column to generate the observation_type='Bird'
            'field': 'observation_type',
            'map': lambda v, r: to_lookup_raise(get_field(model, 'observation_type'), 'Bird')
        },
        'Datum': {
            'field': 'datum',
            'map': lambda x, r: to_model_choice(DATUM_CHOICES, x) if x else None
        },
        'Lat': {
            'field': 'latitude',
            'map': lambda v, r: to_float_raise(only_digit(v)),
        },
        'Long': {
            'field': 'longitude',
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'Accuracy': {
            'field': 'accuracy',
            # turn '50m' into 50.0
            'map': lambda v, r: to_float_raise(only_digit(v))
        },
        'Comments': {
            'field': 'comments',
            'map': lambda v, r: to_string(v)
        }
    }
    return create_model(model, row_data, mapping)


def load_data(file_path=None):
    global current_ws
    if not file_path:
        file_path = path.join(path.dirname(__file__), 'data', DATA_FILE)
    logger.info('Load workbook {}'.format(file_path))
    wb = load_workbook(file_path)
    sheets = wb.get_sheet_names()
    logger.info('Load workbook done')

    current_ws = 'Sites'
    if current_ws in sheets:
        logger.info('Load ' + current_ws + '  worksheet')
        load_sites(wb.get_sheet_by_name(current_ws))
    else:
        logger.warning("No '" + current_ws + "' datasheet.")

    current_ws = 'Visit'
    if current_ws in sheets:
        logger.info('Load ' + current_ws + '  worksheet')
        load_visits(wb.get_sheet_by_name(current_ws))
    else:
        logger.warning("No '" + current_ws + "' datasheet.")

    current_ws = 'Site Characteristics'
    if current_ws in sheets:
        logger.info('Load ' + current_ws + '  worksheet')
        load_site_characteristics(wb.get_sheet_by_name(current_ws))
    else:
        logger.warning("No '" + current_ws + "' datasheet.")

    current_ws = 'Stratum Species'
    if current_ws in sheets:
        logger.info('Load ' + current_ws + '  worksheet')
        load_stratum_species(wb.get_sheet_by_name(current_ws))
    else:
        logger.warning("No '" + current_ws + "' datasheet.")

    current_ws = 'Vegetation'
    if current_ws in sheets:
        logger.info('Load ' + current_ws + '  worksheet')
        load_vegetation(wb.get_sheet_by_name(current_ws))
    else:
        logger.warning("No '" + current_ws + "' datasheet.")

    current_ws = 'Stratum Summary'
    if current_ws in sheets:
        logger.info('Load ' + current_ws + '  worksheet')
        load_stratum_summary(wb.get_sheet_by_name(current_ws))
    else:
        logger.warning("No '" + current_ws + "' datasheet.")

    current_ws = 'Disturbance Indicators'
    if current_ws in sheets:
        logger.info('Load ' + current_ws + '  worksheet')
        load_disturbance_indicators(wb.get_sheet_by_name(current_ws))
    else:
        logger.warning("No '" + current_ws + "' datasheet.")

    current_ws = 'Plant Observation'
    if current_ws in sheets:
        logger.info('Load ' + current_ws + '  worksheet')
        load_plant_observation(wb.get_sheet_by_name(current_ws))
    else:
        logger.warning("No '" + current_ws + "' datasheet.")

    current_ws = 'Biodiversity Indicators'
    if current_ws in sheets:
        logger.info('Load ' + current_ws + '  worksheet')
        load_bio_indicator(wb.get_sheet_by_name(current_ws))
    else:
        logger.warning("No '" + current_ws + "' datasheet.")

    current_ws = 'Trap'
    if current_ws in sheets:
        logger.info('Load ' + current_ws + '  worksheet')
        load_trap(wb.get_sheet_by_name(current_ws))
    else:
        logger.warning("No '" + current_ws + "' datasheet.")

    current_ws = 'Animal Observations'
    if current_ws in sheets:
        logger.info('Load ' + current_ws + '  worksheet')
        load_animal_observations(wb.get_sheet_by_name(current_ws))
    else:
        logger.warning("No '" + current_ws + "' datasheet.")

    current_ws = 'Opportunistic Observations'
    if current_ws in sheets:
        logger.info('Load ' + current_ws + '  worksheet')
        load_opportunistic_observations(wb.get_sheet_by_name(current_ws))
    else:
        logger.warning("No '" + current_ws + "' datasheet.")

    current_ws = 'Birds'
    if current_ws in sheets:
        logger.info('Load ' + current_ws + '  worksheet')
        load_birds_observations(wb.get_sheet_by_name(current_ws))
    else:
        logger.warning("No '" + current_ws + "' datasheet.")

    logger.info('Import Done')


def delete_data():
    # Deleting projects should cascade delete pretty much all the tables
    Project.objects.all().delete()
    # There are some tables without link to project
    OpportunisticObservation.objects.all().delete()
    SpeciesObservation.objects.all().delete()


def run(*args):
    """
    The method called by django-extension runscript
    """
    if 'fresh' in args:
        delete_data()
    file_path = None
    file_ = [arg.split('file=')[1] for arg in args if arg.startswith('file=')]
    if file_:
        file_path = file_[0]
    load_data(file_path=file_path)