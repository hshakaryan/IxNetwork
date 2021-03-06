################################################################################
# Version 1.0    $Revision: 1 $                                                #
#                                                                              #
#    Copyright  1997 - 2015 by IXIA                                            #
#    All Rights Reserved.                                                      #
#                                                                              #
#    Revision Log:                                                             #
#    01/20/2015 - Deepak Kumar Singh - created sample                          #
#                                                                              #
################################################################################

################################################################################
#                                                                              #
#                                LEGAL  NOTICE:                                #
#                                ==============                                #
# The following code and documentation (hereinafter "the script") is an        #
# example script for demonstration purposes only.                              #
# The script is not a standard commercial product offered by Ixia and have     #
# been developed and is being provided for use only as indicated herein. The   #
# script [and all modifications enhancements and updates thereto (whether      #
# made by Ixia and/or by the user and/or by a third party)] shall at all times #
# remain the property of Ixia.                                                 #
#                                                                              #
# Ixia does not warrant (i) that the functions contained in the script will    #
# meet the users requirements or (ii) that the script will be without          #
# omissions or error-free.                                                     #
# THE SCRIPT IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND AND IXIA         #
# DISCLAIMS ALL WARRANTIES EXPRESS IMPLIED STATUTORY OR OTHERWISE              #
# INCLUDING BUT NOT LIMITED TO ANY WARRANTY OF MERCHANTABILITY AND FITNESS FOR #
# A PARTICULAR PURPOSE OR OF NON-INFRINGEMENT.                                 #
# THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE SCRIPT  IS WITH THE #
# USER.                                                                        #
# IN NO EVENT SHALL IXIA BE LIABLE FOR ANY DAMAGES RESULTING FROM OR ARISING   #
# OUT OF THE USE OF OR THE INABILITY TO USE THE SCRIPT OR ANY PART THEREOF     #
# INCLUDING BUT NOT LIMITED TO ANY LOST PROFITS LOST BUSINESS LOST OR          #
# DAMAGED DATA OR SOFTWARE OR ANY INDIRECT INCIDENTAL PUNITIVE OR              #
# CONSEQUENTIAL DAMAGES EVEN IF IXIA HAS BEEN ADVISED OF THE POSSIBILITY OF    #
# SUCH DAMAGES IN ADVANCE.                                                     #
# Ixia will not be required to provide any software maintenance or support     #
# services of any kind (e.g. any error corrections) in connection with the     #
# script or any part thereof. The user acknowledges that although Ixia may     #
# from time to time and in its sole discretion provide maintenance or support  #
# services for the script any such services are subject to the warranty and    #
# damages limitations set forth herein and will not obligate Ixia to provide   #
# any additional maintenance or support services.                              #
#                                                                              #
################################################################################

################################################################################
#                                                                              #
# Description:                                                                 #
#    This script intends to demonstrate how to use NGPF OSPFv3 HLPy API.       #
#                                                                              #
#    1. It will create two OSPFv3 topologies.                                  #
#    2. Configure Network Topologies in each topologies.                       #
#    3. Configure Loopback Device Groups in each topologies.                   #
#    4. Start all protocols.                                                   #
#    5. Retrieve protocol statistics.                                          #
#    6. Configure L2-L3 & Applib traffic items.                                #
#    7. Start the L2-L3 & Applib traffics.                                     #
#    8. Retrieve L2-L3 traffic stats.                                          #
#    9. Make on the fly changes of Inter-Area Prefix attributes                #    
#   10. Retrieve protocol statistics.                                          #
#   11. Stop L2-L3 traffic.                                                    #
#   12. Stop all protocols.                                                    #
#                                                                              #
# Ixia Software:                                                               #
#    IxOS      6.80 EA                                                         #
#    IxNetwork 7.40 EA                                                         #
#                                                                              #
################################################################################

################################################################################
# Utils                                                                        #    
################################################################################

# Libraries to be included
# package require Ixia
# Other procedures used in the script, that do not use HL API configuration/control procedures

from pprint import pprint
import sys, os
import time, re

# Append paths to python APIs (Linux and Windows)

# sys.path.append('/path/to/hltapi/library/common/ixiangpf/python') 
# sys.path.append('/path/to/ixnetwork/api/python')

from ixiatcl import IxiaTcl
from ixiahlt import IxiaHlt
from ixiangpf import IxiaNgpf
from ixiaerror import IxiaError

ixiatcl = IxiaTcl()
ixiahlt = IxiaHlt(ixiatcl)
ixiangpf = IxiaNgpf(ixiahlt)
    
try:
    ErrorHandler('', {})
except (NameError,):
    def ErrorHandler(cmd, retval):
        global ixiatcl
        err = ixiatcl.tcl_error_info()
        log = retval['log']
        additional_info = '> command: %s\n> tcl errorInfo: %s\n> log: %s' % (cmd, err, log)
        raise IxiaError(IxiaError.COMMAND_FAIL, additional_info)        

################################################################################
# Connection to the chassis, IxNetwork Tcl Server                              #
################################################################################
chassis_ip              = ['10.205.28.170']
tcl_server              = '10.205.28.170'
port_list               = [['1/7', '1/8']]
ixnetwork_tcl_server    = '10.205.28.41:8981';
cfgErrors         = 0

print "Printing connection variables ... "
print 'chassis_ip =  %s' % chassis_ip
print "tcl_server = %s " % tcl_server
print "ixnetwork_tcl_server = %s" % ixnetwork_tcl_server
print "port_list = %s " % port_list

print "Connecting to chassis and client"
connect_result = ixiangpf.connect(
        ixnetwork_tcl_server = ixnetwork_tcl_server,
        tcl_server = tcl_server,
        device = chassis_ip,
        port_list = port_list,
        break_locks = 1,
        reset = 1,
    )

if connect_result['status'] != '1':
    ErrorHandler('connect', connect_result)
    
print " Printing connection result"
pprint(connect_result)

#Retrieving the port handles, in a list
ports = connect_result['vport_list'].split()
time.sleep(2)

################################################################################
# Configure Topology, Device Group                                             # 
################################################################################

# Creating a topology on first port
print "Adding topology 1 on port 1" 
_result_ = ixiangpf.topology_config(
    topology_name      = """OSPFv3 Topology 1""",
    port_handle        = ports[0],
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('topology_config', _result_)
    
topology_1_handle = _result_['topology_handle']

# Creating a device group in topology 
print "Creating device group 1 in topology 1"    
_result_ = ixiangpf.topology_config(
    topology_handle              = topology_1_handle,
    device_group_name            = """OSPFv3 Router 1""",
    device_group_multiplier      = "1",
    device_group_enabled         = "1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('topology_config', _result_)
    
deviceGroup_1_handle = _result_['device_group_handle']

# Creating a topology on second port
print "Adding topology 2 on port 2"
_result_ = ixiangpf.topology_config(
    topology_name      = """OSPFv3 Topology 2""",
    port_handle        = ports[1],
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('topology_config', _result_)

topology_2_handle = _result_['topology_handle']

# Creating a device group in topology
print "Creating device group 2 in topology 2"
_result_ = ixiangpf.topology_config(
    topology_handle              = topology_2_handle,
    device_group_name            = """OSPFv3 Router 2""",
    device_group_multiplier      = "1",
    device_group_enabled         = "1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('topology_config', _result_)
deviceGroup_2_handle = _result_['device_group_handle']
time.sleep(2)

################################################################################
#  Configure protocol interfaces                                               #
################################################################################

# Creating ethernet stack for the first Device Group 
print "Creating ethernet stack for the first Device Group"
_result_ = ixiangpf.interface_config(
    protocol_name                = """Ethernet 1""",
    protocol_handle              = deviceGroup_1_handle,
    src_mac_addr                 = "18.03.73.c7.6c.b1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('interface_config', _result_)
    
ethernet_1_handle = _result_['ethernet_handle']

# Creating ethernet stack for the second Device Group
print "Creating ethernet for the second Device Group"
_result_ = ixiangpf.interface_config(
    protocol_name                = """Ethernet 2""",
    protocol_handle              = deviceGroup_2_handle,
    src_mac_addr                 = "18.03.73.c7.6c.01",
 )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('interface_config', _result_)

ethernet_2_handle = _result_['ethernet_handle']

# Creating IPv6 Stack on top of Ethernet Stack for the first Device Group                                 
print "Creating IPv6 Stack on top of Ethernet Stack for the first Device Group"
_result_ = ixiangpf.interface_config(
    protocol_name                = """IPv6 1""",
    protocol_handle              = ethernet_1_handle,
    ipv6_gateway                 = "2000:0:0:1:0:0:0:2",
    ipv6_intf_addr               = "2000:0:0:1:0:0:0:1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('interface_config', _result_)
    
ipv6_1_handle = _result_['ipv6_handle']

# Creating IPv6 Stack on top of Ethernet Stack for the second Device Group 
print "Creating IPv6 2 stack on ethernet 2 stack for the second Device Group"
_result_ = ixiangpf.interface_config(
    protocol_name                = """IPv6 2""",
    protocol_handle              = ethernet_2_handle,
    ipv6_gateway                 = "2000:0:0:1:0:0:0:1",
    ipv6_intf_addr               = "2000:0:0:1:0:0:0:2",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('interface_config', _result_)

ipv6_2_handle = _result_['ipv6_handle']
time.sleep(2)
 
# ###############################################################################
# Configure OSPFv3 protocol                                                     # 
# ###############################################################################

# Creating OSPFv3 Stack on top of IPv6 Stack for the first Device Group
print "Creating OSPFv3 Stack on top of IPv6 1 stack"
_result_ = ixiangpf.emulation_ospf_config(
    handle                                                    = ipv6_1_handle,
    area_id_type                                              = "area_id_as_number",
    router_interface_active                                   = "1",
    protocol_name                                             = """OSPFv3-IF 1""",
    router_active                                             = "1",
    lsa_discard_mode                                          = "0",
    network_type                                              = "ptop",
    mode                                                      = "create",
    session_type                                              = "ospfv3",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_ospf_config', _result_)    
ospfv3_1_handle = _result_['ospfv3_handle']

# Creating OSPFv3 Stack on top of IPv6 Stack for the second Device Group
print "Creating OSPFv3 Stack on top of IPv6 2 stack"
_result_ = ixiangpf.emulation_ospf_config(
    handle                                                    = ipv6_2_handle,
    area_id_type                                              = "area_id_as_number",
    router_interface_active                                   = "1",
    protocol_name                                             = """OSPFv3-IF 2""",
    router_active                                             = "1",
    lsa_discard_mode                                          = "0",
    network_type                                              = "ptop",
    mode                                                      = "create",
    session_type                                              = "ospfv3",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_ospf_config', _result_)    
ospfv3_2_handle = _result_['ospfv3_handle']
time.sleep(2)

# ###############################################################################
# Configure Network Topology & Loopback Device Groups                           # 
# ###############################################################################

# Creating Tree Network Topology in Topology 1
print "Creating Tree Network Topology in Topology 1"
_result_ = ixiangpf.network_group_config(
    protocol_handle                   = deviceGroup_1_handle,
    protocol_name                     = "OSPFv3 Network Group 1",
    multiplier                        = "1",
    enable_device                     = "1",
    type                              = "tree",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('network_group_config', _result_)
networkGroup_1_handle = _result_['network_group_handle']
simRouter_1_handle = _result_['simulated_router_handle']
interAreaPrefix_1_handle = _result_['v3_inter_area_prefix_handle']

print "Creating Loopback Device Group in Topology 1"
_result_ = ixiangpf.topology_config(
    device_group_name            = """Applib Endpoint 1""",
    device_group_multiplier      = "7",
    device_group_enabled         = "1",
    device_group_handle          = networkGroup_1_handle,
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('topology_config', _result_)
deviceGroup_3_handle = _result_['device_group_handle']

_result_ = ixiangpf.multivalue_config(
    pattern                = "counter",
    counter_start          = "3000:0:1:1:0:0:0:0",
    counter_step           = "0:0:0:1:0:0:0:0",
    counter_direction      = "increment",
    nest_step              = "0:0:0:0:0:0:0:1,0:0:0:0:0:0:0:1,0:0:0:1:0:0:0:0",
    nest_owner             = '%s,%s,%s' % (networkGroup_1_handle, deviceGroup_1_handle, topology_1_handle),
    nest_enabled           = "0,0,1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_1_handle = _result_['multivalue_handle']
_result_ = ixiangpf.interface_config(
    protocol_name            = """IPv6 Loopback 1""",
    protocol_handle          = deviceGroup_3_handle,
    enable_loopback          = "1",
    connected_to_handle      = simRouter_1_handle,
    ipv6_intf_addr           = multivalue_1_handle,
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('interface_config', _result_)

# Creating Tree Network Topology in Topology 2
print "Creating Tree Network Topology in Topology 2"
_result_ = ixiangpf.network_group_config(
    protocol_handle                   = deviceGroup_2_handle,
    protocol_name                     = "OSPFv3 Network Group 2",
    multiplier                        = "1",
    enable_device                     = "1",
    type                              = "tree",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('network_group_config', _result_)
networkGroup_2_handle = _result_['network_group_handle']
simRouter_2_handle = _result_['simulated_router_handle']
interAreaPrefix_2_handle = _result_['v3_inter_area_prefix_handle']

print "Creating Loopback Device Group in Topology 2"
_result_ = ixiangpf.topology_config(
    device_group_name            = """Applib Endpoint 2""",
    device_group_multiplier      = "7",
    device_group_enabled         = "1",
    device_group_handle          = networkGroup_2_handle,
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('topology_config', _result_)
deviceGroup_4_handle = _result_['device_group_handle']

_result_ = ixiangpf.multivalue_config(
    pattern                = "counter",
    counter_start          = "3000:5:1:1:0:0:0:0",
    counter_step           = "0:0:0:1:0:0:0:0",
    counter_direction      = "increment",
    nest_step              = "0:0:0:0:0:0:0:1,0:0:0:0:0:0:0:1,0:0:0:1:0:0:0:0",
    nest_owner             = '%s,%s,%s' % (networkGroup_2_handle, deviceGroup_2_handle, topology_2_handle),
    nest_enabled           = "0,0,1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_2_handle = _result_['multivalue_handle']
_result_ = ixiangpf.interface_config(
    protocol_name            = """IPv6 Loopback 2""",
    protocol_handle          = deviceGroup_4_handle,
    enable_loopback          = "1",
    connected_to_handle      = simRouter_2_handle,
    ipv6_intf_addr           = multivalue_2_handle,
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('interface_config', _result_)
time.sleep(2)

# ###########################################################################
# Start all protocols                                                       #
# ###########################################################################
print "Starting all protocols"
_result_ = ixiangpf.test_control(action='start_all_protocols')
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('ixiangpf::traffic_control', _result_)

print "Waiting for 30 seconds for OSPFv3 sessions to come up ..."
time.sleep(30)

# ###############################################################################
# Making on the fly changes for Inter-Area Prefix Network Address in            #
# both Network Topologies                                                       #
# ###############################################################################
# Modifying Inter-Area Prefix Network Address in Network Topology 1
print "Modifying Inter-Area Prefix Network Address in Network Topology 1"
_result_ = ixiangpf.multivalue_config(
    pattern                = "counter",
    counter_start          = "3000:0:1:1:0:0:0:0",
    counter_step           = "0:0:0:1:0:0:0:0",
    counter_direction      = "increment",
    nest_step              = "0:0:0:0:0:0:0:1,0:0:1:0:0:0:0:0",
    nest_owner             = '%s,%s' % (deviceGroup_1_handle, topology_1_handle),
    nest_enabled           = "0,1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)
multivalue_3_handle = _result_['multivalue_handle']

_result_ = ixiangpf.emulation_ospf_network_group_config(
    handle                                      = networkGroup_1_handle,
    mode                                        = "modify",
    inter_area_prefix_active                    = "1",
    inter_area_prefix_network_address           = multivalue_3_handle,
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_ospf_network_group_config', _result_)

# Modifying Inter-Area Prefix Network Address in Network Topology 2
print "Modifying Inter-Area Prefix Network Address in Network Topology 2"
_result_ = ixiangpf.multivalue_config(
    pattern                = "counter",
    counter_start          = "3000:5:1:1:0:0:0:0",
    counter_step           = "0:0:0:1:0:0:0:0",
    counter_direction      = "increment",
    nest_step              = "0:0:0:0:0:0:0:1,0:0:1:0:0:0:0:0",
    nest_owner             = '%s,%s' % (deviceGroup_1_handle, topology_1_handle),
    nest_enabled           = "0,1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)
multivalue_4_handle = _result_['multivalue_handle']

_result_ = ixiangpf.emulation_ospf_network_group_config(
    handle                                      = networkGroup_2_handle,
    mode                                        = "modify",
    inter_area_prefix_active                    = "1",
    inter_area_prefix_network_address           = multivalue_4_handle,
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_ospf_network_group_config', _result_)
time.sleep(2)

################################################################################
# Applying changes one the fly
################################################################################
print "Applying changes on the fly ..."
applyChanges = ixiangpf.test_control(
   action = 'apply_on_the_fly_changes',
)
if applyChanges['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('test_control', applyChanges)

print "Waiting for 15 seconds after applying change on the fly ..."
time.sleep(15)

############################################################################
# Retrieve protocol statistics                                             #
############################################################################
print "Fetching OSPFv3 statistics ..."
protostats = ixiangpf.emulation_ospf_info(
    handle = ospfv3_1_handle,
    session_type = 'ospfv3',
    mode = 'aggregate_stats')
if protostats['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_ospf_info', protostats)

pprint(protostats)
time.sleep(2)

# ########################################################################### 
# Configure L2-3 & L4-7 traffic                                             #
# 1. Endpoints : Source->IPv6, Destination->IPv6                            #
# 2. Type      : Unicast IPv6 traffic                                       #
# 3. Flow Group: On IPv6 Destination Address                                #
# 4. Rate      : 2000 pps                                                   #
# 5. Frame Size: 500 bytes                                                  #
# 6. Tracking  : Source Destination EndpointPair                            #    
# ###########################################################################
# Configuring L2-L3 traffic item
print "Configuring L2-L3 traffic"
_result_ = ixiangpf.traffic_config(
    mode                                        = 'create',
    traffic_generator                           = 'ixnetwork_540',
    endpointset_count                           = 1,
    emulation_src_handle                        = interAreaPrefix_1_handle,
    emulation_dst_handle                        = interAreaPrefix_2_handle,
    name                                        = 'Traffic_Item_1',
    circuit_endpoint_type                       = 'ipv6',
    rate_pps                                    = 2000,                                    
    frame_size                                  = 500,
    track_by                                    = 'sourceDestEndpointPair0 trackingenabled0'
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('traffic_config', _result_)

# Configure traffic for Layer 4-7 AppLibrary Profile
print "Configure L4-7 AppLibrary traffic profile"
_result_ = ixiangpf.traffic_l47_config(
    mode                        = "create",
    name                        = """Traffic Item 2""",
    circuit_endpoint_type       = "ipv6_application_traffic",
    emulation_src_handle        = networkGroup_1_handle,
    emulation_dst_handle        = networkGroup_2_handle,
    objective_type              = "users",
    objective_value             = "100",
    objective_distribution      = "apply_full_objective_to_each_port",
    enable_per_ip_stats         = "0",
    flows                       = """Bandwidth_BitTorrent_File_Download Bandwidth_eDonkey Bandwidth_HTTP Bandwidth_IMAPv4 Bandwidth_POP3 Bandwidth_Radius Bandwidth_Raw Bandwidth_Telnet Bandwidth_uTorrent_DHT_File_Download BBC_iPlayer BBC_iPlayer_Radio BGP_IGP_Open_Advertise_Routes BGP_IGP_Withdraw_Routes Bing_Search BitTorrent_Ares_v217_File_Download BitTorrent_BitComet_v126_File_Download BitTorrent_Blizzard_File_Download BitTorrent_Cisco_EMIX BitTorrent_Enterprise BitTorrent_File_Download BitTorrent_LimeWire_v5516_File_Download BitTorrent_RMIX_5M""",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('traffic_l47_config', _result_)
time.sleep(2)

############################################################################
#  Start Traffic configured earlier                                        #
############################################################################
print "Running Traffic ..."
_result_ = ixiangpf.traffic_control(
    action            = 'run',
    traffic_generator = 'ixnetwork_540',
    type              = 'l23 l47',
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('traffic_control', _result_)

print "Let the traffic run for 30 seconds ..."
time.sleep(30)

############################################################################
# Retrieve Traffic stats                                                   #
############################################################################
print "Retrieving traffic stats ..."
trafficStats = ixiangpf.traffic_stats(
    mode              = 'all',
    traffic_generator = 'ixnetwork_540',
    measure_mode      = 'mixed',
)
if trafficStats['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('traffic_stats', trafficStats)

pprint(trafficStats)
time.sleep(2)

############################################################################
# Stop Traffic started earlier                                             #
############################################################################
print "Stopping Traffic ..."
_result_ = ixiangpf.traffic_control(
    action='stop',
    traffic_generator='ixnetwork_540',
    type='l23 l47',
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('traffic_control', _result_)

time.sleep(2)
    
############################################################################
# Stop all protocols                                                       #
############################################################################
print "Stopping all protocol(s) ..."
_result_ = ixiangpf.test_control(action='stop_all_protocols')
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('test_control', _result_)
time.sleep(2)
       
print "!!! Test Script Ends !!!"
