from flask import abort
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
from openpyxl import load_workbook
from pathlib import Path
import ipaddress
from zipfile import ZipFile

# Folders and file names
DATABASE = 'sqlite:///database/dataloader_db.sqlite?check_same_thread=False'
DATA_FOLDER = Path('served_files/dataloader')
TEMPLATE_FILE = str(DATA_FOLDER / 'Template.xlsx')
R3_DATA_FILE = str(DATA_FOLDER / 'Region 3 Data File.xlsx')
R1_DATA_FILE = str(DATA_FOLDER / 'Region 1 Data File.xlsx')

# Initial configuration of SQLAlchemy engine and connection
Base = automap_base()
engine = create_engine(DATABASE)
Base.prepare(engine, reflect=True)

# Map tables from database
Equipment = Base.classes.equipment_templates
Srx345Ports = Base.classes.srx345_physical_ports
Asr9k = Base.classes.asr9k_routers
PeSite = Base.classes.pe_sites
FacilityVpnPorts = Base.classes.hf_vpn_ports
ServiceVpnPorts = Base.classes.service_vpn_ports
NmsPePorts = Base.classes.nms_pe_ports
ServicePePorts = Base.classes.service_pe_ports
SubnetMasks = Base.classes.subnet_masks

session = Session(engine)


class Port:
    def __init__(self, shelf_name, site_name, vlan, site_type=None, table=None, interface=None, cpe_model=None, bandwidth=None, ip_addr=None, existing=None, nni_port=None, region='3'):
        self.shelf_name = shelf_name
        self.bandwidth = 'UNDEFINED' if bandwidth is None else '{}M'.format(bandwidth)
        self.site_type = 'SINGLE' if site_type is None else site_type
        
        if region == '3':
            self.shelf_name = shelf_name
            self.site_name = site_name
            self.table = '' if table is None else table
            self.interface = '' if interface is None else interface
            if cpe_model is None:
                query = session.query(table).filter(table.shelf_clei == self.shelf_name).first()
            else:
                self.cpe_model = cpe_model
                try:
                    query = session.query(table).filter(
                        table.shelf_clei == cpe_model,
                        table.site_type == self.site_type).first()
                except AttributeError:
                    query = session.query(table).filter(table.physical_interface == vlan).first()
            self.slot_1 = query.slot_1
            self.slot_2 = query.slot_2
            self.slot_3 = query.slot_3
            self.port_id = ''
            if vlan != '' or vlan is None:
                if interface == 'logical':
                    self.port_id = '{port}{vlan}'.format(
                        port=query.logical_interface,
                        vlan=vlan)
                elif interface == 'physical':
                    self.port_id = '{port}{vlan}'.format(
                        port=query.physical_interface,
                        vlan=vlan)
                elif interface == 'loopback':
                    self.port_id = '{port}'.format(port=query.loopback_interface)
                elif interface == 'cpe':
                    self.port_id = '{port}'.format(port=vlan)
                    self.slot_1 = query.slot_1
                    self.slot_2 = query.slot_2
                    self.slot_3 = query.slot_3
                elif interface == 'server':
                    self.port_id = vlan
                    self.slot_1 = query.slot_1
                    self.slot_2 = query.slot_2
                    self.slot_3 = query.slot_3
            self.existing = existing
            self.subnet = None
            self.cidr = None
            if ip_addr is not None:
                self.ip_addr = ip_addr
            else:
                self.ip_addr = None
            self.connector = 'Logical'
            self.network = 'SSHA'
            self.customer = 'C001645'
            self.hostname = 'SSHA'
            
        elif region == '1':
            query = session.query(Asr9k).filter(Asr9k.shelf_clei == shelf_name).first()
            self.site_name = query.shelf_clli
            if interface == 'nni_port':
                self.port_id = '{port}{vlan}'.format(port=nni_port, vlan=vlan)
                self.slot_1 = self.port_id.split('/')[1]
            else:
                if interface == 'primary_vpn_port':
                    port = query.primary_vpn_port
                elif interface == 'backup_vpn_port':
                    port = query.backup_vpn_port
                elif interface == 'nms_port':
                    port = query.nms_port
                
                self.slot_1 = port.split('/')[1]
                if vlan != '':
                    self.port_id = '{port}{vlan}'.format(port=port, vlan=vlan)
                else:
                    self.port_id = ''
            self.connector = 'LOGICAL'

    # Parameter 'place' will be either 1 or 2 (for first or second IP in sub range)
    # If IP address is a blank value, ignore it and continue. Otherwise, throw an invalid IP error and abort
    def get_ip(self, network_addr, cidr, place):
        if int(cidr) == 31:
            try:
                # Subtract 1 from 'place' parameter if CIDR is 31 (there are only 2 addresses in a /31 range)
                self.ip_addr = str(ipaddress.ip_address(network_addr) + (int(place) - 1))
            except ValueError:
                # Allow empty value (will simply ignore it), otherwise abort if invalid IP
                if network_addr == '':
                    pass
                else:
                    abort(400, 'Invalid IP: {addr} /{cidr}'.format(
                        addr=network_addr,
                        cidr=cidr))
        else:
            try:
                self.ip_addr = str(ipaddress.ip_address(network_addr) + place)
            except ValueError:
                if network_addr == '':
                    pass
                else:
                    abort(400, 'Invalid IP: {addr} /{cidr}'.format(
                        addr=network_addr,
                        cidr=cidr))


class Shelf(Port):
    def __init__(self, shelf_name, site_name, shelf_template, ip_addr=None):
        self.shelf_name = shelf_name
        self.site_name = site_name
        self.shelf_template = shelf_template
        self.ip_addr = ip_addr if ip_addr is not None else None


class Subnet:
    def __init__(self, network_addr, cidr, notes):
        self.network = 'SSHA'
        self.sub_start = network_addr
        self.sub_end = ''
        if int(cidr) == 31:
            self.cidr = ''
            try:
                self.sub_end = str(ipaddress.ip_address(network_addr) + 1)
            except ValueError:
                pass
        else:
            self.cidr = cidr
        self.status = 'ACTIVE'
        self.notes = notes


class Channel:
    def __init__(self, shelf, vlan, path, bandwidth=None, region='3'):
        self.path_name = ''
        if region == '3':
            query = session.query(PeSite).filter(PeSite.shelf_clei == shelf).first()
        elif region == '1' and path != 'vendor':
            query = session.query(Asr9k).filter(Asr9k.shelf_clei == shelf).first()
                      
        if path == 'pe_vpn_path':
            self.path_name = query.pe_vpn_path
        elif path == 'facility_path':
            self.path_name = query.facility_path
        elif path == 'nms_path':
            self.path_name = query.nms_path
        elif path == 'vendor_path':
            self.path_name = shelf
            
        if vlan == '':
            self.channel_name = ''
        else:
            self.channel_name = 'VLAN{}'.format(vlan)

        self.bandwidth = 'UNDEFINED' if bandwidth is None else '{}M'.format(bandwidth)
        self.channel_status = 'Ok'


# Take form data as argument
def create_r3_data_file(d):
    # Load template and assign sheets to variables
    wb = load_workbook(TEMPLATE_FILE)
    SHELF_SHEET = wb['SHELF']
    PORT_SHEET = wb['PORT']
    SUBNET_SHEET = wb['SUBNET']
    IP_SHEET = wb['IP']
    CHANNEL_SHEET = wb['CHANNEL']

    shelf_rows = {}
    port_rows = {}
    subnet_rows = []
    channel_rows = []

    try:
        site_type = d['siteType']
    except KeyError:
        abort(400, 'Invalid site type')

    try:
        site_clli = d['siteCLLI']
    except KeyError:
        abort(400, 'Invalid site CLLI')

    try:
        p_pe_router = d['peRouter1']
        query = session.query(PeSite).filter(PeSite.shelf_clei == p_pe_router).first()
        p_pe_site = query.pop_clli
        p_vpn_primary = query.vpn_primary
        p_vpn_backup = query.vpn_backup
    except KeyError:
        abort(400, 'Invalid PE router')

    try:
        p_bw_minus = int(d['siteBandwidth']) - 1
    except ValueError:
        abort(400, 'Invalid site bandwidth')
    except KeyError:
        abort(400, 'Invalid site bandwidth')

    try:
        site_router = d['cpeRouter']
    except KeyError:
        abort(400, 'Invalid CPE router')

    try:
        site_router_template = d['cpeTemplate']
    except KeyError:
        abort(400, 'Invalid CPE template')

    # Validate all mandatory dual CPE fields
    if site_type == 'dual':
        try:
            ter_server = d['terServer']
        except KeyError:
            abort(400, 'Invalid terminal server')

        try:
            server_template = d['terServerTemplate']
        except KeyError:
            abort(400, 'Invalid server template')

        try:
            b_pe_router = d['peRouter2']
            query = session.query(PeSite).filter(PeSite.shelf_clei == b_pe_router).first()
            b_pe_site = query.pop_clli
            b_vpn_primary = query.vpn_primary
            b_vpn_backup = query.vpn_backup
        except KeyError:
            abort(400, 'Invalid backup PE router')

        try:
            b_bw_minus = int(d['backupBandwidth']) - 1
        except ValueError:
            abort(400, 'Invalid backup site bandwidth')
        except KeyError:
            abort(400, 'Invalid backup site bandwidth')

    # SHELF SHEET
    row_counter = 2  # Row counter will be reset to 2 at the start of every sheet (Row 1 for column headers)

    # CPE Router
    shelf_rows.update({'p_cpe': Shelf(site_router, site_clli, site_router_template)})
    try:
        port_rows.update({'loopback': Port(
            shelf_name=site_router,
            site_name=site_clli,
            vlan=1,  # Used as placeholder to pass VLAN check of empty string
            table=Equipment,
            interface='loopback',
            cpe_model=d['modelName'],
            ip_addr=d['cpeLoopback'])}
        )
    except KeyError:
        pass

    # Terminal Server
    if site_type == 'dual':
        shelf_rows.update({'ter_serv': Shelf(d['terServer'], site_clli, d['terServerTemplate'])})
        port_rows.update({
            'ter_server1': Port(
                shelf_name=ter_server,
                site_name=site_clli,
                site_type=site_type.upper(),                
                vlan=1,
                table=Equipment,
                interface='server',
                cpe_model=server_template,
                existing=True
            ),

            'ter_server2': Port(
                shelf_name=ter_server,
                site_name=site_clli,
                site_type=site_type.upper(),                
                vlan=2,
                table=Equipment,
                interface='server',
                cpe_model=server_template,
                existing=True
            )
        })
        # Assign first IP (network address) of sub range to port 1
        port_rows['ter_server1'].get_ip(
            network_addr=d['terServerIP'],
            cidr=d['terServerCIDR'],
            place=0
        )
        # Assign last IP (broadcast address) of sub range to port 2
        port_rows['ter_server2'].get_ip(
            network_addr=d['terServerIP'],
            cidr=d['terServerCIDR'],
            place=4
        )

    # Print equipment to shelf sheet
    for key, value in shelf_rows.items():
        if value.shelf_name != '' or value.shelf_name is not None:  # Don't print row if shelf name is empty
            SHELF_SHEET['A{}'.format(row_counter)] = value.shelf_name
            SHELF_SHEET['B{}'.format(row_counter)] = value.site_name
            SHELF_SHEET['C{}'.format(row_counter)] = value.shelf_template
        row_counter += 1

    # PORT SHEET
    row_counter = 2

    # Primary single ports which do not require looping
    port_rows.update({
        'p_nms_pe': Port(
            shelf_name=p_pe_router,
            site_name=p_pe_site,
            vlan=d['nmsVlan'],
            table=NmsPePorts,
            interface='logical',
            bandwidth=1
        ),

        'p_nms_cpe': Port(
            shelf_name=site_router,
            site_name=site_clli,
            vlan=d['nmsVlan'],
            table=Equipment,
            interface='logical',
            cpe_model=d['modelName'],
            bandwidth=1
        ),

        'p_hf_cpe': Port(
            shelf_name=site_router,
            site_name=site_clli,
            vlan=d['facilityVlan'],
            table=Equipment,
            interface='logical',
            cpe_model=d['modelName'],
            bandwidth=p_bw_minus
        )
    })

    # IP's are optional, skip IP assignment if no IP is provided
    port_rows['p_nms_pe'].get_ip(
        network_addr=d['nmsIP'],
        cidr=d['nmsCIDR'],
        place=1
    )

    port_rows['p_nms_cpe'].get_ip(
        network_addr=d['nmsIP'],
        cidr=d['nmsCIDR'],
        place=2
    )

    port_rows['p_hf_cpe'].get_ip(
        network_addr=d['facilityIP'],
        cidr=d['facilityCIDR'],
        place=2
    )

    # Backup single ports which do not require looping
    if site_type == 'dual':
        port_rows.update({
            'b_nms_pe': Port(
                shelf_name=b_pe_router,
                site_name=b_pe_site,
                vlan=d['nmsVlanBackup'],
                table=NmsPePorts,
                interface='logical',
                bandwidth=1
            ),

            'b_nms_cpe': Port(
                shelf_name=site_router,
                site_name=site_clli,
                site_type=site_type.upper(),
                vlan=d['nmsVlanBackup'],
                table=Equipment,
                interface='logical',
                cpe_model=d['modelName'],
                bandwidth=1
            ),

            'b_hf_cpe': Port(
                shelf_name=site_router,
                site_name=site_clli,
                site_type=site_type.upper(),
                vlan=d['facilityVlanBackup'],
                table=Equipment,
                interface='logical',
                cpe_model=d['modelName'],
                bandwidth=b_bw_minus
            )
        })
        # Backup single IP's
        # IP's are optional, skip IP assignment if no IP is provided
        port_rows['b_nms_pe'].get_ip(
            network_addr=d['nmsIPBackup'],
            cidr=d['nmsCIDRBackup'],
            place=1
        )

        port_rows['b_nms_cpe'].get_ip(
            network_addr=d['nmsIPBackup'],
            cidr=d['nmsCIDRBackup'],
            place=2
        )

        port_rows['b_hf_cpe'].get_ip(
            network_addr=d['facilityIPBackup'],
            cidr=d['facilityCIDRBackup'],
            place=2
        )

    # BEGIN PRIMARY HOT FACILITY VPN PORTS #
    # Primary HOT Facility VPN Ports
    vpn_routers = [p_vpn_primary, p_vpn_backup]
    interfaces = ['physical', 'logical']
    suffix = 1

    for vpn in vpn_routers:  # Loop through both SRX's
        for interface in interfaces:   # Loop through physical and logical port of each SRX
            port_rows.update({
                'p_hf_vpn{}'.format(suffix): Port(
                    shelf_name=vpn,
                    site_name=p_pe_site,
                    vlan=d['facilityVlan'],
                    table=FacilityVpnPorts,
                    interface=interface,
                    bandwidth=p_bw_minus
                )
            })
            # IP address goes on logical port (reth) of primary SRX
            if vpn == p_vpn_primary and interface == 'logical':
                port_rows['p_hf_vpn{}'.format(suffix)].get_ip(
                    network_addr=d['facilityIP'],
                    cidr=d['facilityCIDR'],
                    place=1
                )
            suffix += 1

    # Primary Service Ports
    suffix = 1  # Suffix of HTML element names
    counter = 1  # Increment names of entries in port_rows
    for i in range(int(d['numServices'])):
        vlan = '' if suffix == 1 else suffix  # If suffix is 1, remove suffix from HTML element name

        port_rows.update({
            # Service PE Ports
            'p_service_pe{}'.format(counter): Port(
                shelf_name=p_pe_router,
                site_name=p_pe_site,
                vlan=d['serviceVlan{}'.format(vlan)],
                table=ServicePePorts,
                interface='logical'
            ),
            # Service CPE Port
            'p_service_cpe{}'.format(counter): Port(
                shelf_name=site_router,
                site_name=site_clli,
                vlan=d['servicePort{}'.format(vlan)],
                table=Srx345Ports,
                interface='cpe',
                cpe_model=d['modelName'],
                existing=True)
        })
        # IP's are optional, skip IP assignment if no IP is provided
        port_rows['p_service_pe{}'.format(counter)].get_ip(
            network_addr=d['servicePeIP{}'.format(vlan)],
            cidr=d['servicePeCIDR{}'.format(vlan)],
            place=1
        )

        port_rows['p_service_cpe{}'.format(counter)].get_ip(
            network_addr=d['serviceCpeIP{}'.format(vlan)],
            cidr=d['serviceCpeCIDR{}'.format(vlan)],
            place=1
        )

        # While in this loop, create Service subnets and channels
        # Service Subnets
        subnet_rows.extend([
            Subnet(
                network_addr=d['servicePeIP{}'.format(vlan)],
                cidr=d['servicePeCIDR{}'.format(vlan)],
                notes='Service PE - VPN'
            ),
            Subnet(
                network_addr=d['serviceCpeIP{}'.format(vlan)],
                cidr=d['serviceCpeCIDR{}'.format(vlan)],
                notes='Service CPE'
            )
        ])

        # Service Channels
        channel_rows.extend([Channel(
            vlan=d['serviceVlan{}'.format(vlan)],
            shelf=p_pe_router,
            path='pe_vpn_path')]
        )

        # Service VPN Ports
        for vpn in vpn_routers:
            for interface in interfaces:
                port_rows.update({'p_service_vpn{}'.format(counter): Port(
                    shelf_name=vpn,
                    site_name=p_pe_site,
                    vlan=d['serviceVlan{}'.format(vlan)],
                    table=ServiceVpnPorts,
                    interface=interface)}
                )
                # IP Address goes on physical port of primary SRX
                if vpn == p_vpn_primary and interface == 'physical':
                    port_rows['p_service_vpn{}'.format(counter)].get_ip(
                        network_addr=d['servicePeIP{}'.format(vlan)],
                        cidr=d['servicePeCIDR{}'.format(vlan)],
                        place=2)
                counter += 1
        suffix += 1

    # BEGIN BACKUP HOT FACILITY AND SERVICE PORTS #
    # Backup HOT Facility VPN Ports
    if site_type == 'dual':
        vpn_routers = [b_vpn_primary, b_vpn_backup]
        interfaces = ['physical', 'logical']
        suffix = 1

        for vpn in vpn_routers:  # Loop through both SRX's
            for interface in interfaces:  # Loop through physical and logical port of each SRX
                port_rows.update({'b_hf_vpn{}'.format(suffix): Port(
                    shelf_name=vpn,
                    site_name=b_pe_site,
                    vlan=d['facilityVlanBackup'],
                    table=FacilityVpnPorts,
                    interface=interface,
                    bandwidth=b_bw_minus)}
                )
                # IP address goes on logical port (reth) of primary SRX
                if vpn == b_vpn_primary and interface == 'logical':
                    port_rows['b_hf_vpn{}'.format(suffix)].get_ip(
                        network_addr=d['facilityIPBackup'],
                        cidr=d['facilityCIDRBackup'],
                        place=1
                    )
                suffix += 1

        # Backup Service Ports
        suffix = 1  # Suffix of HTML element names
        counter = 1  # Increment names of entries in port_rows
        for i in range(int(d['numServices'])):
            vlan = '' if suffix == 1 else suffix  # If suffix is 1, remove suffix from HTML element name

            # Service PE Ports
            port_rows.update({'b_service_pe{}'.format(counter): Port(
                shelf_name=b_pe_router,
                site_name=b_pe_site,
                vlan=d['serviceVlanBackup{}'.format(vlan)],
                table=ServicePePorts,
                interface='logical')}
            )
            # IP's are optional, skip IP assignment if no IP is provided
            port_rows['b_service_pe{}'.format(counter)].get_ip(
                network_addr=d['servicePeIPBackup{}'.format(vlan)],
                cidr=d['servicePeCIDRBackup{}'.format(vlan)],
                place=1)

            # While in this loop, create Service subnets and channels
            # Service Subnets
            subnet_rows.extend([Subnet(
                network_addr=d['servicePeIPBackup{}'.format(vlan)],
                cidr=d['servicePeCIDRBackup{}'.format(vlan)],
                notes='Service PE - VPN (backup)')]
            )

            # Service Channels
            channel_rows.extend([Channel(
                vlan=d['serviceVlanBackup{}'.format(vlan)],
                shelf=b_pe_router,
                path='pe_vpn_path')]
            )

            # Service VPN Ports
            for vpn in vpn_routers:
                for interface in interfaces:
                    port_rows.update({'b_service_vpn{}'.format(counter): Port(
                        shelf_name=vpn,
                        site_name=b_pe_site,
                        vlan=d['serviceVlanBackup{}'.format(vlan)],
                        table=ServiceVpnPorts,
                        interface=interface)}
                    )
                    # IP Address goes on physical port of primary SRX
                    if vpn == b_vpn_primary and interface == 'physical':
                        port_rows['b_service_vpn{}'.format(counter)].get_ip(
                            network_addr=d['servicePeIPBackup{}'.format(vlan)],
                            cidr=d['servicePeCIDRBackup{}'.format(vlan)],
                            place=2
                        )
                    counter += 1
            suffix += 1
            # END BACKUP HOT FACILITY AND SERVICE PORTS #

    # Print port rows
    # Does not print if port id is empty or its existing parameter is set to false (ports created from template)
    suffix_counter = 1  # Counter for all service ports
    for key, value in port_rows.items():
        if value.port_id != '' and not value.existing:
            PORT_SHEET['A{}'.format(row_counter)] = value.shelf_name
            PORT_SHEET['B{}'.format(row_counter)] = value.site_name
            PORT_SHEET['C{}'.format(row_counter)] = value.slot_1
            if value.slot_2 != '':
                PORT_SHEET['D{}'.format(row_counter)] = value.slot_2
            if value.slot_3 != '':
                PORT_SHEET['E{}'.format(row_counter)] = value.slot_3
            PORT_SHEET['F{}'.format(row_counter)] = value.port_id
            PORT_SHEET['G{}'.format(row_counter)] = value.bandwidth
            PORT_SHEET['H{}'.format(row_counter)] = value.connector
            row_counter += 1
            suffix_counter += 1

    # Subnet Sheet
    row_counter = 2

    # Primary single subnets which do not need to be looped
    subnet_rows.extend([
        # NMS Subnet
        Subnet(
            network_addr=d['nmsIP'],
            cidr=d['nmsCIDR'],
            notes='NMS PE - CPE'
        ),

        # HOT Facility Subnet
        Subnet(
            network_addr=d['facilityIP'],
            cidr=d['facilityCIDR'],
            notes='HOT Facility VPN - CPE'
        )
    ])

    # Backup single subnets which do not need to be looped
    if site_type == 'dual':
        subnet_rows.extend([
            # NMS Subnet
            Subnet(
                network_addr=d['nmsIPBackup'],
                cidr=d['nmsCIDRBackup'],
                notes='NMS PE - CPE (backup)'
            ),

            # HOT Facility Subnet
            Subnet(
                network_addr=d['facilityIPBackup'],
                cidr=d['facilityCIDRBackup'],
                notes='HOT Facility VPN - CPE (backup)'
            ),

            # Terminal Server Subnet
            Subnet(
                network_addr=d['terServerIP'],
                cidr=d['terServerCIDR'],
                notes='Terminal Server'
            )
        ])

    for value in subnet_rows:
        if value.sub_start != '':
            SUBNET_SHEET['A{}'.format(row_counter)] = value.network
            SUBNET_SHEET['B{}'.format(row_counter)] = value.sub_start
            if value.cidr != '':
                SUBNET_SHEET['C{}'.format(row_counter)] = value.cidr
            if value.sub_end != '':
                SUBNET_SHEET['D{}'.format(row_counter)] = value.sub_end
            SUBNET_SHEET['E{}'.format(row_counter)] = value.status
            SUBNET_SHEET['F{}'.format(row_counter)] = value.notes
            row_counter += 1

    # IP Sheet
    # All IP's were assigned during port creation
    row_counter = 2
    for key, value in port_rows.items():
        if value.ip_addr is not None and value.ip_addr != '':  # Only print ports that have an IP address to IP sheet
            IP_SHEET['A{}'.format(row_counter)] = value.shelf_name
            IP_SHEET['B{}'.format(row_counter)] = value.site_name
            IP_SHEET['C{}'.format(row_counter)] = value.slot_1
            if value.slot_2 != '':
                IP_SHEET['D{}'.format(row_counter)] = value.slot_2
            if value.slot_3 != '':
                IP_SHEET['E{}'.format(row_counter)] = value.slot_3
            IP_SHEET['F{}'.format(row_counter)] = value.port_id
            IP_SHEET['G{}'.format(row_counter)] = value.ip_addr
            IP_SHEET['H{}'.format(row_counter)] = value.network
            IP_SHEET['I{}'.format(row_counter)] = value.customer
            IP_SHEET['J{}'.format(row_counter)] = value.hostname
            row_counter += 1

    # Channel Sheet
    row_counter = 2

    # Primary management channels
    channel_rows.extend([
        # NMS Channel
        Channel(
            vlan=d['nmsVlan'],
            shelf=p_pe_router,
            path='nms_path',
            bandwidth=1
        ),

        # Facility Channel
        Channel(
            vlan=d['facilityVlan'],
            shelf=p_pe_router,
            path='facility_path',
            bandwidth=p_bw_minus
        )
    ])

    # Backup Management channels
    if site_type == 'dual':
        channel_rows.extend([
            Channel(
                vlan=d['nmsVlanBackup'],
                shelf=b_pe_router,
                path='nms_path',
                bandwidth=1
            ),

            Channel(
                vlan=d['facilityVlanBackup'],
                shelf=b_pe_router,
                path='facility_path',
                bandwidth=b_bw_minus
            )
        ])

    # Service channels are created in port section
    for value in channel_rows:
        if value.path_name != '' and value.channel_name != '':
            CHANNEL_SHEET['A{}'.format(row_counter)] = value.path_name
            CHANNEL_SHEET['B{}'.format(row_counter)] = value.channel_name
            CHANNEL_SHEET['C{}'.format(row_counter)] = value.bandwidth
            CHANNEL_SHEET['D{}'.format(row_counter)] = value.channel_status
            row_counter += 1

    try:
        wb.save(R3_DATA_FILE)
    except PermissionError:
        abort(400, 'Permission denied. Data file is either already open or insufficient permissions to write to file.')
        

def create_r1_data_file(d):
    # Load template and assign sheets to variables
    wb = load_workbook(TEMPLATE_FILE)
    PORT_SHEET = wb['PORT']
    CHANNEL_SHEET = wb['CHANNEL']

    port_rows = []
    channel_rows = []
    
    p_bw_minus = int(d['siteBandwidth']) - 1
    b_bw_minus = int(d['backupBandwidth']) - 1
    asr_ports = ['primary_vpn_port', 'backup_vpn_port', 'nms_port']
    asr_paths = ['facility_path', 'nms_path']
    
    query = session.query(PeSite).filter(PeSite.shelf_clei == d['peRouter1']).first()
    asr9k = session.query(Asr9k).filter(Asr9k.shelf_clli == query.pop_clli).first()

    for port in asr_ports:
        if port == 'nms_port':
            vlan = d['nmsVlan']
            bandwidth = 1
        else:
            vlan = d['facilityVlan']
            bandwidth = p_bw_minus

        port_rows.append(Port(
            shelf_name=asr9k.shelf_clei,
            site_name=asr9k.shelf_clli,
            vlan=vlan,
            bandwidth=bandwidth,
            interface=port,
            region='1'
        ))
        
    # Primary
    for path in asr_paths:
        if path == 'nms_path':
            vlan = d['nmsVlan']
            bandwidth = 1
        else:
            vlan = d['facilityVlan']
            bandwidth = p_bw_minus

        channel_rows.append(Channel(
            shelf=asr9k.shelf_clei,
            vlan=vlan,
            path=path,
            bandwidth=bandwidth,
            region='1'
        ))
        
        # Primary Vendor NNI interface
        try:
            if d['vendorInterface'] and d['vendorPort']:
                nni_port = '{interface}{port}.'.format(interface=d['vendorInterface'], port=d['vendorPort'])
                port_rows.append(Port(
                    shelf_name=asr9k.shelf_clei,
                    site_name=asr9k.shelf_clli,
                    vlan=vlan,
                    bandwidth=bandwidth,
                    interface='nni_port',
                    nni_port=nni_port,
                    region='1',
                ))
        except KeyError:
            pass
        
    # Backup
    if d['siteType'] == 'dual':
        query = session.query(PeSite).filter(PeSite.shelf_clei == d['peRouter2']).first()
        if d['peRouter2'] == 'TOROONXNPED10' or query.pop_clli == 'TOROONXNPED11':
            clli = 'TOROONXND27'
        else:
            clli = query.pop_clli
        asr9k = session.query(Asr9k).filter(Asr9k.shelf_clli == clli).first()
        
        for port in asr_ports:
            if port == 'nms_port':
                vlan = d['nmsVlanBackup']
                bandwidth = 1
            else:
                vlan = d['facilityVlanBackup']
                bandwidth = b_bw_minus
    
            port_rows.append(Port(
                shelf_name=asr9k.shelf_clei,
                site_name=asr9k.shelf_clli,
                vlan=vlan,
                bandwidth=bandwidth,
                interface=port,
                region='1'
            ))
            
        for path in asr_paths:
            if path == 'nms_path':
                vlan = d['nmsVlanBackup']
                bandwidth = 1
            else:
                vlan = d['facilityVlanBackup']
                bandwidth = p_bw_minus
    
            channel_rows.append(Channel(
                shelf=asr9k.shelf_clei,
                vlan=vlan,
                path=path,
                bandwidth=bandwidth,
                region='1'
            ))
        

            # Backup Vendor NNI interface
            try:
                if d['vendorInterfaceBackup'] and d['vendorPortBackup']:
                    nni_port = '{interface}{port}.'.format(interface=d['vendorInterfaceBackup'], port=d['vendorPortBackup'])
                    port_rows.append(Port(
                        shelf_name=asr9k.shelf_clei,
                        site_name=asr9k.shelf_clli,
                        vlan=vlan,
                        bandwidth=bandwidth,
                        interface='nni_port',
                        nni_port=nni_port,
                        region='1',
                    ))
            except KeyError:
                pass
            
            

    row_counter = 2
    for item in port_rows:
        if item.port_id != '':
            PORT_SHEET['A{}'.format(row_counter)] = item.shelf_name
            PORT_SHEET['B{}'.format(row_counter)] = item.site_name
            PORT_SHEET['C{}'.format(row_counter)] = item.slot_1
            PORT_SHEET['F{}'.format(row_counter)] = item.port_id
            PORT_SHEET['G{}'.format(row_counter)] = item.bandwidth
            PORT_SHEET['H{}'.format(row_counter)] = item.connector
            row_counter += 1
           
    # Primary vendor channel        
    if d['vendorChannel'] and d['vendorVlan']:
        channel_rows.append(Channel(
            shelf=d['vendorChannel'],
            vlan=d['vendorVlan'],
            path='vendor_path',
            bandwidth=d['siteBandwidth'],
            region='1'
        ))
        
    if d['siteType'] == 'dual':
        if d['vendorChannelBackup'] and d['vendorVlanBackup']:
            channel_rows.append(Channel(
                shelf=d['vendorChannelBackup'],
                vlan=d['vendorVlanBackup'],
                path='vendor_path',
                bandwidth=d['siteBandwidth'],
                region='1'
            ))
        
    


    row_counter = 2
    for value in channel_rows:
        if value.path_name != '' and value.channel_name != '':
            CHANNEL_SHEET['A{}'.format(row_counter)] = value.path_name
            CHANNEL_SHEET['B{}'.format(row_counter)] = value.channel_name
            CHANNEL_SHEET['C{}'.format(row_counter)] = value.bandwidth
            CHANNEL_SHEET['D{}'.format(row_counter)] = value.channel_status
            row_counter += 1

    wb.save(R1_DATA_FILE)


def zip_data_files(d):
    create_r3_data_file(d)
    create_r1_data_file(d)
    
    site_clli = d['siteCLLI']

    with ZipFile(str(DATA_FOLDER / 'Data Files.zip'), 'w') as z:
        z.write(R1_DATA_FILE, arcname='Region 1 - {} Data File.xlsx'.format(site_clli))
        z.write(R3_DATA_FILE, arcname='Region 3 - {} Data File.xlsx'.format(site_clli))


def dropdown_lists():
    lists = {
        'pe_routers': [i.shelf_clei for i in session.query(PeSite.shelf_clei)],
        'router_templates': [i.template_name for i in session.query(Equipment.template_name)
                             .filter(Equipment.equipment_type == 'ROUTER')
                             ],
        'server_templates': [i.template_name for i in session.query(Equipment.template_name)
                             .filter(Equipment.equipment_type == 'SERVER')
                             ],
        'cidr_prefixes': list(reversed([i.cidr_prefix for i in session.query(SubnetMasks.cidr_prefix)])),
        'srx345_node0_ports': [i.physical_interface for i in session.query(Srx345Ports.physical_interface)
                               .filter(Srx345Ports.shelf_node == 'NODE 0')
                               ]
    }
    # Prevent duplicate router models from being printed to list
    model_names = []
    for i in session.query(Equipment).filter(Equipment.equipment_type == 'ROUTER'):
        if i.shelf_clei not in model_names:
            model_names.append(i.shelf_clei)
    lists.update({'model_names': model_names})

    return lists


if __name__ == '__main__':
    form = {
        'peRouter1': 'OTWBONPZPED10',
        'siteBandwidth': 100,
        'facilityVlan': '640',
        'nmsVlan': '639',
        'vendorInterface': 'GIG',
        'vendorPort': '0/1/0/18',
        'vendorChannel': '0001-10GIG-E-OTWBONPZPED01-OTWBONPZD00-ROGERS',
        'vendorVlan': '600-601',
        'siteBandwidthBackup': 50,
        'peRouter2': 'TOROONXNPED10',
        'siteType': 'dual',
        'facilityVlanBackup': '990',
        'nmsVlanBackup': '989',
        'vendorInterfaceBackup': 'TEN',
        'vendorPortBackup': '0/1/0/69',
        'vendorChannelBackup': '0005-10GIG-E-OTWBONPZPED01-OTWBONPZD00-ROGERS',
        'vendorVlanBackup': '1000-1001',
    }
    
    zip_data_files(form)

