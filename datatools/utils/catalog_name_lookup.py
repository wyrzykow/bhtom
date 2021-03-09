from collections import OrderedDict
from logging import Logger, getLogger
from typing import Dict, List, Optional

from tom_targets.models import Target

from astroquery.simbad import Simbad

import requests
from django.conf import settings
from lxml import html

logger: Logger = getLogger(__name__)
alert_name_keys: Dict[str, str] = settings.ALERT_NAME_KEYS


def get_tns_id_from_gaia_name(gaia_name: str) -> Optional[str]:
    try:
        alert_url: str = f'{settings.GAIA_ALERT_URL}/{gaia_name}'
        logger.info(f'[Name fetch for {gaia_name}] Attempting to read TNS ID from {alert_url}')
        result = requests.get(alert_url)
        status_code: Optional[int] = getattr(result, 'status_code', None)

        if status_code == 200:
            tree = html.fromstring(result.content)
            tns_ids = tree.xpath("//dt[text()='TNS ID']/following::dd/a/text()")
            if tns_ids and len(tns_ids) > 0:
                logger.info(f'[Name fetch for {gaia_name}] Found TNS ID {tns_ids}')
                return tns_ids[0]
        else:
            if status_code:
                logger.error(f'[Name fetch for {gaia_name}] Error when requesting the URL. Returned status code: {status_code}')
            else:
                logger.error(f'[Name fetch for {gaia_name}] No result for request')

    except Exception as e:
        logger.error(f'Error while looking up TNS ID for {gaia_name}: {e}')
        return None


def get_tns_id(target: Target) -> Optional[str]:
    """
    Queries the TNS server and returns a dictionary with
    ztf_alert_name and gaia_alert_name, if found
    """
    import json

    try:
        logger.info(f'[Name fetch for {target.name}] Attempting to query TNS...')
        target_url: str = f'{settings.TNS_URL}/search'
        logger.info(f'[Name fetch for {target.name}] Requesting {target_url}...')
        api_key: str = settings.TNS_API_KEY

        search_json = {
            "ra": str(target.ra),
            "dec": str(target.dec),
            "objname": "",
            "objname_exact_match": 0,
            "internal_name": str(target.name),
            "internal_name_exact_match ": 0,
        }
        search_data = [('api_key', (None, api_key)),
                       ('data', (None, json.dumps(OrderedDict(search_json))))]

        # search obj using request module
        response = requests.post(target_url, files=search_data)
        logger.info(f'[Name fetch for {target.name}] TNS response with status {response.status_code} '
                    f'and content {response.content.decode("utf-8")}')
        response_data: Dict[str, str] = json.loads(response.content.decode("utf-8"))['data']['reply'][0]
        logger.info(f'[Name fetch for {target.name}] Read names as {response_data["prefix"]}{response_data["objname"]}')
        return f'{response_data["prefix"]}{response_data["objname"]}'
    except Exception as e:
        logger.error(f'[Name fetch for {target.name}] Error while querying TNS server: {e}')
        return None


def get_tns_internal(tns_id: str) -> Dict[str, str]:
    """
    Queries the TNS server and returns a dictionary with
    ztf_alert_name and gaia_alert_name, if found
    """
    import json

    try:
        logger.info(f'[Name fetch for {tns_id}] Attempting to query TNS...')
        target_url: str = f'{settings.TNS_URL}/object'
        logger.info(f'[Name fetch for {tns_id}] Requesting {target_url}...')
        api_key: str = settings.TNS_API_KEY

        search_json = {
            "objname": tns_id_to_url_slug(tns_id),
            "objname_exact_match": 1,
            "photometry": "0",
            "spectra": "0"
        }

        search_data = [('api_key', (None, api_key)),
                       ('data', (None, json.dumps(OrderedDict(search_json))))]
        # search obj using request module
        response = requests.post(target_url, files=search_data)

        logger.info(f'[Name fetch for {tns_id}] Returned response with status code {response.status_code} '
                    f'and content {response.content.decode("utf-8")}')
        internal_names: List[str] = [n.strip() for n in
                                     json.loads(response.content.decode("utf-8"))['data']['reply'][
                                         'internal_names'].split(',')]
        logger.info(f'[Name fetch for {tns_id}] Read internal names as {internal_names}')

        result_dict: Dict[str, str] = {}

        for internal_name in internal_names:
            matched_group: List[str] = assign_group_to_internal_name(internal_name)
            logger.info(f'[Name fetch for {tns_id}] Attempting to read internal name for {matched_group}...')

            if len(matched_group) > 0:
                try:
                    result_dict[matched_group[0][0]] = internal_name
                    logger.info(f'[Name fetch for {tns_id}] Read internal name for {matched_group[0][0]}: {internal_name}')
                except:
                    continue

        return result_dict
    except Exception as e:
        logger.error(f'[Name fetch for {tns_id}] Error while querying TNS server: {e}')
        return {}


def query_simbad_for_names(target: Target) -> Dict[str, str]:
    from astropy.table import Table
    import re

    try:
        logger.info(f'[Name fetch for {target.name}] Querying Simbad for target {target.name}...')

        result_table: Optional[Table] = Simbad.query_objectids(object_name=target.name)
        result_dict: Dict[str] = {}

        if result_table:
            logger.info(f'[Name fetch for {target.name}] Returned Simbad query table...')

            for row in result_table['ID']:
                if 'AAVSO' in row:
                    logger.info(f'[Name fetch for {target.name}] Found AAVSO name...')
                    result_dict[alert_name_keys['AAVSO']] = re.sub(r'^AAVSO( )*', '', row)
                elif 'Gaia DR2' in row:
                    logger.info(f'[Name fetch for {target.name}] Found Gaia DR2 name...')
                    result_dict[alert_name_keys['GAIA DR2']] = re.sub(r'^Gaia( )*DR2( )*', '', row)

        return result_dict
    except Exception as e:
        logger.error(f'[Name fetch for {target.name}] Error while querying Simbad for target {target.name}: {e}')
        return {}


def tns_id_to_url_slug(tns_id: str) -> str:
    import re

    return re.sub(r'^([A-Z])+( )*', '', tns_id)


def assign_group_to_internal_name(name: str) -> List[str]:
    import re

    name_regex = re.compile('(^([A-Z]|[a-z])+)')
    return name_regex.findall(name)


def tns_internal_name_xpath(group_name: str) -> str:
    return f'//tr[td[@class="cell-groups" and text()="{group_name}"]]/td[@class="cell-internal_name"]/text()'
