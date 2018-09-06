from flask import abort
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
from pathlib import Path
from zipfile import ZipFile
from datetime import date
import ipaddress

# Folders and file names
DATABASE = 'sqlite:///database/config_generator_db.sqlite?check_same_thread=False'
BASE_PATH = Path('served_files/config_generator')
TEMPLATES_PATH = Path().resolve() / BASE_PATH / 'templates'

# File names of templates in templates folder
cpe_template = '1 - Single CPE.txt'
dual_cpe_template = '1 - Dual CPE.txt'
cpe_service_template = '1 - Single CPE (Service).txt'
dual_cpe_service_template = '1 - Dual CPE (Service).txt'
switch_template = '2 - L2 Switch.txt'
vpn_template = '3 - VPN.txt'
vpn_service_template = '3 - VPN (Service).txt'
pe_template = '4 - PE.txt'
pe_service_template = '4 - PE (Service).txt'
ipsla_template = '5 - IPSLA.txt'
ipsla_primary_template = '5 - IPSLA (Primary).txt'
ipsla_backup_template = '5 - IPSLA (Backup).txt'

# Initial configuration of SQLAlchemy engine and connection
Base = automap_base()
engine = create_engine(DATABASE)
Base.prepare(engine, reflect=True)

PeSites = Base.classes.pe_sites
Lhin = Base.classes.lhin_sites
VpnServices = Base.classes.vpn_services
EquipList = Base.classes.equipment_list
EquipPorts= Base.classes.equipment_ports
Cidr = Base.classes.subnet_masks
Speeds = Base.classes.port_speeds

session = Session(engine)


# If site id is in the format of ###.6##, change the 6 to a 7
def get_backup_site(site):
    try:
        split = site.split('.')
        backup = split[1].replace('6','.7')
        backup_site_id = split[0] + backup
        return backup_site_id
    except IndexError:
        return site


# Strip all leading and trailing whitespaces from form values
def strip_whitespace(d):
    stripped_form = {}
    
    try:
        for key, value in d.items():
            stripped = str(value.strip())
            stripped_form.update({key: stripped})
    except KeyError:
        abort(400, 'Invalid entry. Please check your inputs and try again. \nField: {key} \nInput: {value}'.format(
            key=key,
            value=value)
        )
    except ValueError:
        abort(400, 'Invalid entry. Please check your inputs and try again. \nField: {key} \nInput: {value}'.format(
            key=key,
            value=value)
        )
    
    return stripped_form
        

# Format the headers for config files
def make_header(header_text):
    columns = 51
    header_buns = '=' * columns  # Top and bottom
    header_sides = '-' * int((columns-len(header_text)) / 2)
    header_body = '{}{}{}'.format(header_sides, header_text, header_sides)
    header = ("{}\n{}\n{}".format(header_buns, header_body, header_buns))
    return header


# Create lists to populate dropdown lists of HTML 
def dropdown_lists(device=None):
    lists = {}

    lists.update({
        'services': [i.service_name for i in session.query(VpnServices)],
        'pe_routers': [i.pe_router for i in session.query(PeSites)],
        'cidr': list(reversed([i.cidr_prefix for i in session.query(Cidr)])),
        'port_speeds': [i.speed_mbps for i in session.query(Speeds)],
        'lhin': ['{id} - {name}'.format(id=i.lhin_id, name=i.lhin_name)
                 for i in session.query(Lhin)
                 ],
    })
    counter = 0  # Counter for switching between primary and backup (0 for primary ports, 1 for backup)

    # Query related tables to retrieve the ports which match device type chosen
    # Assumes column names in equipment_ports table follows the format: (device_type)_(primary/backup)
    # e.g. srx345_primary
    if device:
        primary = '{}_primary'.format(device)
        backup = '{}_backup'.format(device)
        ports = [primary, backup]
        for port in ports:
            if counter == 0:
                lists.update({'primary_ports': [getattr(i, port) for i in session.query(EquipPorts)]})
            else:
                lists.update({'backup_ports': [getattr(i, port) for i in session.query(EquipPorts)]})
            counter += 1
    
    return lists


# Load template files
def render_from_template(directory, template_name, **kwargs):
    """
    Render a template and make replacements based on arguments provided
    """
    loader = FileSystemLoader(directory)
    env = Environment(loader=loader)
    template = env.get_template(template_name)
    return template.render(**kwargs)


def create_key_list(form, pe_router, site_type=None):
    """
    Create and return a key_list for rendering of templates and making replacements.

    All variables used in templates will be from key_list dictionary. (key_list is split up into sections for 
    readability and updating purposes.)
    """
    d = strip_whitespace(form)
    key_list = {}
    
    # Database queries to be reused throughout function
    pe_query = session.query(PeSites).filter(PeSites.pe_router == pe_router.upper()).first()
    lhin_query = session.query(Lhin).filter(Lhin.lhin_id == int(d['lhinID'][:2])).first()
    equip_query = session.query(EquipList).filter(EquipList.equipment_name == d['deviceHidden'].upper()).first()
    
    if site_type == 'b':
        site = 'Backup' 
        uplink_port = equip_query.uplink_port_backup.lower()
    else:
        site = ''
        uplink_port = equip_query.uplink_port_primary.lower()
    
    # Section - Header keys
    key_list.update({
        'cpe_header': make_header(d['equipmentName']),
        'switch_header': make_header(pe_query.asr_name),
        'vpn_header': make_header(pe_query.srx3600_name),
        'pe_header': make_header(pe_router.upper()),
        'p_ipsla_header': make_header(lhin_query.ip_sla_primary),
        'b_ipsla_header': make_header(lhin_query.ip_sla_backup)
    })

    # Section - General site info keys
    key_list.update({
        'cpe_service_configs': [],
        'dual_cpe_service_configs': [],
        'pe_service_configs': [],
        'pop_clli': pe_query.pop_clli,
        'logical_pe_port': pe_query.pe_logical_port,
        'cpe_router': d['equipmentName'],
        'loopback_ip': d['loopbackIP'],
        'msu_id': d['msuID' + site],
        'site_id': d['siteID'],
        'bw_minus_one': int(d['siteBandwidth' + site]) - 1,
        'uplink_port': uplink_port,
        'uplink_port_speed': '{}M'.format(d['uplinkPortSpeed' + site]),
        'stag_vlan': d['sTagVlan' + site],
        'clfi': '0001-{bw}M-{site}-{cpe}'.format(
            bw=d['siteBandwidth' + site],
            site=pe_query.pop_clli,
            cpe=d['equipmentName']
        ),
    })

    # Section - NMS keys
    # Change trunk config lines depending on S-TAG VLAN input
    if d['sTagVlan' + site] == '':
        nms_trunk_config = 'encapsulation dot1q {}'.format(d['nmsVlan' + site])
        vpn_trunk_config = 'encapsulation dot1q {}'.format(d['vpnConcVlan' + site])
    else:
        nms_trunk_config = 'encapsulation dot1q {stag} second-dot1q {vlan}'.format(
            stag=d['sTagVlan' + site],
            vlan=d['nmsVlan' + site]
        )
        vpn_trunk_config = 'encapsulation dot1q {stag} second-dot1q {vlan}'.format(
            stag=d['sTagVlan' + site],
            vlan=d['vpnConcVlan' + site]
        )

    key_list.update({
        'nms_vlan': d['nmsVlan' + site],
        'nms_pe_ip': ipaddress.ip_address(d['nmsIP' + site]),
        'nms_cpe_ip': ipaddress.ip_address(d['nmsIP' + site]) + 1,
        'nms_cidr': 31,
        'nms_trunk_config': nms_trunk_config,
        'nms_path': 'NMS-{}'.format(d['equipmentName']),
        'nms_pe_port': pe_query.pe_nms_port,
        'asr_nms_port': '{port}.{vlan}'.format(
            port=pe_query.asr_nms_port,
            vlan=d['nmsVlan' + site]
        ),
        'asr_nms_nni_port': '{port}.{vlan}'.format(
            port=d['vendorInterface' + site] + d['vendorPort' + site],
            vlan=d['nmsVlan' + site]
        ),
    })

    # Section - VPN keys
    key_list.update({
        'vpn_service_configs': [],
        'vpn_conc': pe_query.srx3600_name,
        'vpn_vlan': d['vpnConcVlan' + site],
        'vpn_vpn_ip': ipaddress.ip_address(d['vpnConcIP' + site]),
        'vpn_cpe_ip': ipaddress.ip_address(d['vpnConcIP' + site]) + 1,
        'vpn_cidr': 31,
        'vpn_trunk_config': vpn_trunk_config,
        'vpn_path': '0001-{bw}M-{vpn}-{cpe}'.format(
            bw=int(d['siteBandwidth' + site]) - 1,
            vpn=pe_query.srx3600_name,
            cpe=d['equipmentName']
        ),
        'asr_45w_port': '{port}.{vlan}'.format(
            port=pe_query.asr_45w_port,
            vlan=d['vpnConcVlan' + site]
        ),
        'asr_46w_port': '{port}.{vlan}'.format(
            port=pe_query.asr_46w_port,
            vlan=d['vpnConcVlan' + site]
        ),
        'asr_vpn_nni_port': '{port}.{vlan}'.format(
            port=d['vendorInterface' + site] + d['vendorPort' + site],
            vlan=d['vpnConcVlan' + site]
        ),
    })

    # Section - IP SLA keys
    key_list.update({
            'primary_ipsla_configs': [],
            'backup_ipsla_configs': [],
            'primary_ipsla_router': lhin_query.ip_sla_primary,
            'backup_ipsla_router': lhin_query.ip_sla_backup
        })
    
    # Loop for number of services
    # Each loop will create one service's configs and append the results to their respective keys in key_list
    counter = 1  # Increment through HTML elements of services
    service_template_list = {
        'cpe_service_configs': cpe_service_template,
        'vpn_service_configs': vpn_service_template,
        'pe_service_configs': pe_service_template,
        'primary_ipsla_configs': ipsla_primary_template,
        'backup_ipsla_configs': ipsla_backup_template
    }
    if site_type == 'b':
        service_template_list.update({'dual_cpe_service_configs': dual_cpe_service_template})
    for i in range(int(d['numServicesHidden'])):
        # Reset service_keys at start of every loop
        service_keys = {}  # Keys will be appended to service_keys in sections for readability and ease of updating
        suffix = '' if counter == 1 else counter  # First service HTML elements are not suffixed with an increment

        cpe_port = d['servicePort{}{}'.format(site, suffix)].lower()
        # All references to query below except for IP SLA will be the query of pe_sites table row matching PE router
        service_query = session.query(VpnServices).filter(VpnServices.service_name == d['serviceType{}{}'.format(site, suffix)]).first()

        # Section - Site info keys
        service_keys.update({
            'msu_id': key_list['msu_id'],
            'site_id': key_list['site_id'].split('.')[0],  # Only get first portion of site ID
            'vpn_conc': key_list['vpn_conc'],
            'cpe_router': key_list['cpe_router'],
            'bw_minus_one': key_list['bw_minus_one'],
            'vpn_vlan': key_list['vpn_vlan'],
        })

        # Section - General service keys
        service_keys.update({
            'service_type': d['serviceType{}{}'.format(site, suffix)],
            'ipsec_abbrev': service_query.ipsec_abbreviation,
            'cpe_asn': service_query.cpe_asn,
            'vpn_asn': service_query.vpn_asn,
            'route_target': service_query.route_target,
            'srx_exchange': service_query.srx_exchange,
            'vlan': d['serviceVlan{}{}'.format(site, suffix)],
            'tunnel_id': cpe_port[7:],  # Remove first 7 characters from cpe port to get tunnel ID
            'pe_logical_port': pe_query.pe_logical_port,
            'clci': d['serviceCLCI{}{}'.format(site, suffix)]
        })

        # Section - CPE (User interface) keys
        service_keys.update({
            'cpe_router': key_list['cpe_router'],
            'cpe_port': cpe_port,
            'cpe_port_speed': d['servicePortSpeed{}{}'.format(site, suffix)],
            'cpe_ip': ipaddress.ip_address(d['serviceCpeIP{}{}'.format(site, suffix)]) + 1,
            'cpe_cidr': d['serviceCpeCIDR{}{}'.format(site, suffix)],
        })

        # Section - PE (PE - VPN interface) keys
        service_keys.update({
            'pe_network': d['servicePeIP{}{}'.format(site, suffix)],
            'pe_ip': ipaddress.ip_address(d['servicePeIP{}{}'.format(site, suffix)]) + 1,
            'vpn_ip': ipaddress.ip_address(d['servicePeIP{}{}'.format(site, suffix)]) + 2,
            'pe_cidr': 30,
            'pe_45w_port': pe_query.pe_45w_port,
            'pe_46w_port': pe_query.pe_46w_port
        })

        # Section - IP SLA keys
        ipsla_query = session.query(VpnServices).filter(VpnServices.service_name == d['serviceType{}{}'.format(site, suffix)]).first()
        service_keys.update({
                'ipsla_vrf': ipsla_query.ip_sla_vrf_name,
                'primary_ipsla_entry': d['serviceIPSLA{}{}'.format(site, suffix)],
                'backup_ipsla_entry': d['serviceIPSLABackup{}{}'.format(site, suffix)]               
        })
        
        # Append results of rendered service templates into their respective config keys
        # Loop through all service configs and their templates
        for config, template in service_template_list.items():
            key_list[config].append(render_from_template(
                directory=str(TEMPLATES_PATH),
                template_name=template,
                key=service_keys
            ))

        counter += 1
    
    return key_list


def generate_configs(form, p_pe_router, b_pe_router=None):

    text_area_configs = {}  # Will contain outputs of configs for printing to text area HTML elements on success page
    key_lists = {'primary': create_key_list(form=form, pe_router=p_pe_router)}

    # Change list of templates according to site type
    if b_pe_router:
        key_lists.update({'backup': create_key_list(form=form, pe_router=b_pe_router, site_type='b')})

        templates = {
            '1 - CPE': cpe_template,
            '2 - L2 Switch': switch_template,
            '3 - VPN': vpn_template,
            '4 - PE': pe_template,
            '5 - IPSLA': ipsla_template,
            '1 - Dual CPE (Backup)': dual_cpe_template,
            '2 - L2 Switch (Backup)': switch_template,
            '3 - VPN (Backup)': vpn_template,
            '4 - PE (Backup)': pe_template
        }

        # Condense IP SLA configs into 1 file
        key_lists['primary']['primary_ipsla_configs'].append(key_lists['backup']['primary_ipsla_configs'][0])
        key_lists['primary']['backup_ipsla_configs'].append(key_lists['backup']['backup_ipsla_configs'][0])
    else:
        templates = {
            '1 - CPE': cpe_template,
            '2 - L2 Switch': switch_template,
            '3 - VPN': vpn_template,
            '4 - PE': pe_template,
            '5 - IPSLA': ipsla_template,
        }

    site_id = form['siteID']
    
    # Create new config zip in zip_archive
    zip_name = 'Site {id} Configs - {date}.zip'.format(id=site_id, date=str(date.today()))
    zip_file = str(BASE_PATH / zip_name)
    ZipFile(zip_file, 'w')

    for config, template in templates.items():
        if '(Backup)' not in config:
            key_list = key_lists['primary']
            file_name = '{id} - {config}.txt'.format(id=site_id, config=config)
        else:
            key_list = key_lists['backup']
            file_name = '{id} - {config}.txt'.format(id=get_backup_site(site_id), config=config)

        results = render_from_template(
            directory=str(TEMPLATES_PATH),
            template_name=template,
            key=key_list
        )

        # Save the rendered template as plain string for printing to HTML textarea elements
        text_area_configs.update({config: results})

        # Write results into new text file
        with ZipFile(zip_file, 'a') as zf:
            zf.writestr(file_name, results)

    # Update dictionary with header title and file name of zip
    text_area_configs.update({'config_zip': zip_name})

    return text_area_configs


if __name__ == '__main__':
    test_form = {
        'siteBandwidth': '100', 
        'serviceBandwidthBackup': '49', 
        'uplinkPortSpeedBackup': '100', 
        'siteID': '343.601',
        'vpnConcIPBackup': '0.0.0.0', 
        'serviceVlan': '100', 
        'serviceIPSLABackup': '50069',
        'sTagVlanBackup': '', 
        'rethInterfaceBackup': 'reth20', 
        'serviceType': 'CCAC', 
        'nmsVlan': '100', 
        'vpnConcVlanBackup': '201', 
        'vendorPort': '0/0/0/0', 
        'serviceCLCIBackup': 'clci2', 
        'serviceCpeCIDR': '30', 
        'serviceCpeCIDRBackup': '30', 
        'msuIDBackup': 'MSUID123B', 
        'serviceVlanBackup': '400',
        'serviceCpeIP': '0.0.0.0', 
        'servicePort': 'GE-0/0/8',
        'servicePeIPBackup': '0.0.0.0', 
        'serviceHosts': '',
        'msuID': 'MSUID123A',
        'vendorInterface': 'TenGigabitEthernet', 
        'servicePortBackup': 'GE-5/0/9',
        'lhinID': '11 - Champlain', 
        'serviceIPSLABackupBackup': '600069',
        'numServicesHidden': '1', 
        'servicePeIP': '0.0.0.0', 
        'vendorPortBackup': '1/1/1/1', 
        'nmsIPBackup': '0.0.0.0', 
        'sTagVlan': '1515', 
        'deviceHidden': 'srx345', 
        'serviceCLCI': 'clci', 
        'servicePortSpeed': '100', 
        'siteTypeHidden': 'dual', 
        'nmsVlanBackup': '200', 
        'serviceCpeIPBackup': '0.0.0.0',
        'servicePortSpeedBackup': '100',
        'nmsIP': '0.0.0.0', 
        'rethInterface': 'reth0', 
        'serviceIPSLA': '10069', 
        'serviceBandwidth': '99',
        'vpnConcVlan': '101',
        'serviceTypeBackup': 'CCAC-VoIP',
        'siteBandwidthBackup': '50', 
        'uplinkPortSpeed': '100',
        'serviceHostsBackup': '', 
        'loopbackIP': '127.0.0.1',
        'vendorInterfaceBackup': 'GigabitEthernet',
        'vpnConcIP': '0.0.0.0', 
        'equipmentName': 'CLEI'  
    }
    
    router = 'TOROONXNPED10'
    b_router = 'ebckoncbped10'
    generate_configs(test_form, router, b_router)
    pass
