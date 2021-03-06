################################################################################
# Version 1.0    $Revision: 1 $                                                #
#                                                                              #
#    Copyright  1997 - 2016 by IXIA                                            #
#    All Rights Reserved.                                                      #
#                                                                              #
#    Revision Log:                                                             #
#    30/06/2016 - Poulomi Chatterjee - created sample                          #
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
#    This script intends to demonstrate how to use NGPF EVPN VxLAN HLPy API.   #
#                                                                              #
# 1. It will create 2 EVPN VxLAN topologies in following way.                  #
#   - Configure OSPF in connected Devicr Group to Advertise Loopback Address   #
#       of BGP.                                                                #
#   - Configure Network Groups behind each Device Groups.                      #
#   - Add chained Device Group behind each Network Group, add IPv4 Loopback in #
#      these Device Groups.                                                    #
#   - Configure BGP Peer over IPv4 Loopback .                                  #
#   - Configure EVI(VxLAN) stack over BGP.                                     #
#   - Configure MAC Pools behing EVPN VxLAN Device Group.                      #
#   - Add IPv4/IPv6 Prefixes in Mac Pools.                                     #
#   - Configure BGP C-MAC Properties                                           #
# 2. Start all protocol.                                                       #
# 3. Retrieve protocol statistics.                                             #
# 4. Retrieve protocol learned info.                                           #
# 5. Configure L2-L3 traffic (with End Point Types: Ethernet & IPv4).          #
# 6. Start the L2-L3 traffic.                                                  #
# 7. Retrieve L2-L3 traffic stats.                                             #
# 8. Stop L2-L3 traffic.                                                       #
# 9. Stop allprotocols.                                                        #
#                                                                              #
# Ixia Software:                                                               #
#    IxOS      8.10-EB                                                         #
#    IxNetwork 8.10-EB                                                         #
#                                                                              #
################################################################################

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
chassis_ip              = ['10.216.108.82']
tcl_server              = '10.216.108.82'
port_list               = [['7/5', '7/6']]
ixnetwork_tcl_server    = '10.216.104.58:8335';
cfgErrors               = 0

print "Printing connection variables ... "
print 'chassis_ip =  %s' % chassis_ip
print "tcl_server = %s " % tcl_server
print "ixnetwork_tcl_server = %s" % ixnetwork_tcl_server
print "port_list = %s " % port_list

print "Connect to chassis ..."
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

################################################################################
# Creating topology and device group                                           #
################################################################################

# Creating a topology in first port
print ('Adding topology:1 in port 1')    
_result_ = ixiangpf.topology_config(
        topology_name      = """EVPN-VxLAN Topology 1""",
        port_handle        = ports[0],
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('topology_config', _result_)
    
topology_1_handle = _result_['topology_handle']

# Creating a device group in topology 1
print "Creating device group 1 in topology 1\n"
_result_ = ixiangpf.topology_config(
        topology_handle              = topology_1_handle,
        device_group_name            = """Provider Router 1""",
        device_group_multiplier      = "1",
        device_group_enabled         = "1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('topology_config', _result_)
    
deviceGroup_1_handle = _result_['device_group_handle']
    
# Creating a topology in second port
print "Adding topology 2 in port 2"    
_result_ = ixiangpf.topology_config(
        topology_name      = """EVPN-VxLAN Topology 2""",
        port_handle        = ports[1],
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('topology_config', _result_)
    
topology_2_handle = _result_['topology_handle']

# Creating a device group in topology 2
print "Creating device group 2 in topology 2"    
_result_ = ixiangpf.topology_config(
        topology_handle              = topology_2_handle,
        device_group_name            = """Provider Router 2""",
        device_group_multiplier      = "1",
        device_group_enabled         = "1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('topology_config', _result_)
    
deviceGroup_4_handle = _result_['device_group_handle']

################################################################################
#  Configure protocol interfaces                                               #
################################################################################

# Creating ethernet stack in device group 1
print "Creating ethernet stack in first device group 1" 
_result_ = ixiangpf.interface_config(
        protocol_name                = """Ethernet 1""",
        protocol_handle              = deviceGroup_1_handle,
        mtu                          = "1500",
        src_mac_addr                 = "18.03.73.c7.6c.b2",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('interface_config', _result_)
    
ethernet_1_handle = _result_['ethernet_handle']

# Creating ethernet stack in device group 2
print "Creating ethernet stack in second device group 2"
_result_ = ixiangpf.interface_config(
        protocol_name                = """Ethernet 2""",
        protocol_handle              = deviceGroup_4_handle,
        mtu                          = "1500",
        src_mac_addr                 = "18.03.73.c7.6c.b1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('interface_config', _result_)

ethernet_2_handle = _result_['ethernet_handle']

    
# Creating IPv4 Stack on top of Ethernet Stack 1
print "Creating IPv4  stack on first ethernet stack 1" 
_result_ = ixiangpf.interface_config(
        protocol_name                     = """IPv4 1""",
        protocol_handle                   = ethernet_1_handle,
        ipv4_resolve_gateway              = "1",
        ipv4_manual_gateway_mac           = "00.00.00.00.00.01",
        ipv4_manual_gateway_mac_step      = "00.00.00.00.00.00",
        gateway                           = "20.20.20.1",
        intf_ip_addr                      = "20.20.20.2",
        netmask                           = "255.255.255.0",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('interface_config', _result_)
    
ipv4_1_handle = _result_['ipv4_handle']
    
# Creating IPv4 Stack on top of Ethernet Stack 2
print "Creating IPv4  stack on second ethernet stack 2"
_result_ = ixiangpf.interface_config(
        protocol_name                     = """IPv4 2""",
        protocol_handle                   = ethernet_2_handle,
        ipv4_resolve_gateway              = "1",
        ipv4_manual_gateway_mac           = "00.00.00.00.00.01",
        gateway                           = "20.20.20.2",
        intf_ip_addr                      = "20.20.20.1",
        netmask                           = "255.255.255.0",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('interface_config', _result_)

ipv4_2_handle = _result_['ipv4_handle']

################################################################################
# Configure EVPN-VxLAN Topologies in both ports as described in Description    #
#  section above.                                                              #
################################################################################
    
#Creating OSPF Stack on top of ipv4 1 stack
print "Creating OSPF Stack on top of ipv4 1 stack\n"
_result_ = ixiangpf.emulation_ospf_config(
      handle                        = ipv4_1_handle,
      router_interface_active       = "1",
      protocol_name                 = """OSPFv2-IF 1""",
      router_active                 = "1",
      network_type                  = "ptop",
      router_id                     = "192.0.0.1",
      mode                          = "create",
)

if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_ospf_config', _result_)

ospfv2_1_handle = _result_['ospfv2_handle']
 
#Adding IPv4 Prefix Pools behind first DG in Port1
print "Adding IPv4 Prefix Pools behind first DG in Port1\n";
_result_ = ixiangpf.network_group_config(
      protocol_handle                       = deviceGroup_1_handle,
      protocol_name                         = """PE Loopback Address Pool 1""",
      multiplier                            = "1",
      enable_device                         = "1",
      connected_to_handle                   = ethernet_1_handle,
      type                                  = "ipv4-prefix",
      ipv4_prefix_network_address           = "2.2.2.2",
      ipv4_prefix_network_address_step      = "0.0.0.1",
      ipv4_prefix_length                    = "32",
      ipv4_prefix_multiplier                = "2",
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('network_group_config', _result_)   

ipv4PrefixPools_1_handle = _result_['ipv4_prefix_pools_handle']
networkGroup_1_handle = _result_['network_group_handle'] 

# Configuring OSPF Prefix Pool Parameters in Port1
print "Configuring OSPF Prefix Pool Parameters in Port1\n"
_result_ = ixiangpf.emulation_ospf_network_group_config(
      handle                           = networkGroup_1_handle,
      mode                             = "modify",
      ipv4_prefix_metric               = "0",
      ipv4_prefix_active               = "1",
      ipv4_prefix_route_origin         = "another_area",
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_ospf_network_group_config', _result_)

# Add VTEP behind IPv4 Prefix Pool 1
print "Add VTEP behind IPv4 Prefix Pool 1\n"
_result_ = ixiangpf.topology_config(
      device_group_name            = """VTEP 1""",
      device_group_multiplier      = "2",
      device_group_enabled         = "1",
      device_group_handle          = networkGroup_1_handle,
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('topology_config', _result_)

deviceGroup_2_handle = _result_['device_group_handle']

_result_ = ixiangpf.multivalue_config(
      pattern                = "counter",
      counter_start          = "2.2.2.2",
      counter_step           = "0.0.0.1",
      counter_direction      = "increment",
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_1_handle = _result_['multivalue_handle']

# Add ipv4 loopback in DG2
print "Add ipv4 loopback in DG2\n";
_result_ = ixiangpf.interface_config(
      protocol_name            = """IPv4 Loopback 1""",
      protocol_handle          = deviceGroup_2_handle,
      enable_loopback          = "1",
      connected_to_handle      = networkGroup_1_handle,
      intf_ip_addr             = multivalue_1_handle,
      netmask                  = "255.255.255.255",
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('interface_config', _result_)

ipv4Loopback_1_handle = _result_['ipv4_loopback_handle']

# Adding BGP peer over ipv4 Loopback 1
print "Adding BGP peer over ipv4 Loopback 1\n";

# Add multivalue to configure IRB MAC Address
_result_ = ixiangpf.multivalue_config (
     pattern                = "counter",
     counter_start          = "00:01:03:00:00:01",
     counter_step           = "00:00:00:00:00:01",
     counter_direction      = "increment",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_2_handle = _result_['multivalue_handle']

# Add multivalue to configure Remote IP Address
_result_ = ixiangpf.multivalue_config (
    pattern                = "counter",
    counter_start          = "3.2.2.2",
    counter_step           = "0.0.0.1",
    counter_direction      = "increment",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_3_handle = _result_['multivalue_handle']

_result_ = ixiangpf.emulation_bgp_config(
      mode                                    = "enable",
      active                                  = "1",
      handle                                  = ipv4Loopback_1_handle,
      ip_version                              = "4",
      remote_ip_addr                          = multivalue_3_handle,
      count                                   = "1",
      local_router_id                         = "2.2.2.2",
      ethernet_segments_count                 = "1",
      filter_evpn                             = "1",
      evpn                                    = "1",
      routers_mac_or_irb_mac_address          = multivalue_2_handle,
      operational_model                       = "symmetric",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_config', _result_)

bgpIpv4Peer_1_handle = _result_['bgp_handle']

# Add EVPN VxLAN stack on top of BGP in Port1
print "Add EVPN VxLAN stack on top of BGP in Port1\n"
_result_ = ixiangpf.emulation_bgp_route_config(
      handle      = bgpIpv4Peer_1_handle,
      mode        = "create",
      evpn_vxlan        = "1",
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_route_config', _result_)

bgpIPv4EvpnVXLAN_1_handle = _result_['evpn_evi']

# Configure BGP Ethernet Segment stack in Port1
print "Configure BGP Ethernet Segment stack in Port1\n"
_result_ = ixiangpf.emulation_bgp_config(
      mode                                               = "modify",
      handle                                             = bgpIpv4Peer_1_handle,
      active_ethernet_segment                            = "1",
      esi_type                                           = "type0",
      esi_value                                          = "1",
      include_mac_mobility_extended_community            = "0",
      support_multihomed_es_auto_discovery               = "1",
      auto_configure_es_import                           = "1",
      support_fast_convergence                           = "1",
      enable_single_active                               = "0",
      advertise_inclusive_multicast_route                = "1",
      evis_count                                         = "2",
      ethernet_segment_name                              = """BGP Ethernet Segment 2""",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_config', _result_)

# Configure EVI parameters in Port1
print "Configure EVI parameters in Port1\n"

# Adding multivalue_9 to configure -ad_route_labels
_result_ = ixiangpf.multivalue_config (
    pattern                = "counter",
    counter_start          = "1001",
    counter_step           = "1",
    counter_direction      = "increment",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_9_handle = _result_['multivalue_handle']

# Adding multivalue_10 to configure -upstream_downstream_assigned_mpls_label
_result_ = ixiangpf.multivalue_config (
    pattern                = "counter",
    counter_start          = "3001",
    counter_step           = "1",
    counter_direction      = "increment",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_10_handle = _result_['multivalue_handle']

_result_ = ixiangpf.emulation_bgp_route_config(
      handle                                           = bgpIpv4Peer_1_handle,
      mode                                             = "modify",
      ad_route_label                                   = multivalue_9_handle,
      upstream_downstream_assigned_mpls_label          = multivalue_10_handle,
      evpn_vxlan                                       = "1",
      no_of_mac_pools                                  = "1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_route_config', _result_)

# Create MAC/IP Pool behind PE Router 1
print "Create MAC/IP Pool behind PE Router 1\n"

_result_ = ixiangpf.multivalue_config (
    pattern                = "counter",
    counter_start          = "22.22.22.22.22.22",
    counter_step           = "00.00.00.01.00.00",
    counter_direction      = "increment",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_16_handle = _result_['multivalue_handle']

_result_ = ixiangpf.multivalue_config(
	pattern                = "counter",
	counter_start          = "22.22.22.22.22.22",
	counter_step           = "00.00.00.01.00.00",
	counter_direction      = "increment",
)
if _result_['status'] != IxiaHlt.SUCCESS:
	ixnHLT_errorHandler('multivalue_config', _result_)
multivalue_14_handle = _result_['multivalue_handle']

_result_ = ixiangpf.network_group_config(
      protocol_handle                       = deviceGroup_2_handle,
      protocol_name                         = "Hosts_1",
      multiplier                            = "1",
      enable_device                         = "1",
      connected_to_handle                   = bgpIPv4EvpnVXLAN_1_handle,
      type                                  = "mac-ipv4-prefix",
      mac_pools_multiplier                  = "5",
      mac_pools_prefix_length               = "48",
      mac_pools_mac                         = multivalue_16_handle,
      ipv4_prefix_network_address           = "201.1.0.1",
      ipv4_prefix_network_address_step      = "0.1.0.0",
      ipv4_prefix_length                    = "32",
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('network_group_config', _result_)

macPools_1_handle = _result_['mac_pools_handle']
ipv4PrefixPools_2_handle = _result_['ipv4_prefix_pools_handle']
networkGroup_4_handle = _result_['network_group_handle']

# Configure BGP properties in MAC Pool
print "Configure BGP properties in MAC Pool\n"

_result_ =  ixiangpf.multivalue_config (
    pattern                = "counter",
    counter_start          = "4001",
    counter_step           = "1",
    counter_direction      = "increment",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_17_handle = _result_['multivalue_handle']


_result_ = ixiangpf.emulation_bgp_route_config(
    handle                         = networkGroup_4_handle,
    mode                           = "create",
    active                         = "1",
    max_route_ranges               = "1",
    label_step                     = "1",
    advertise_ipv4_address         = "1",
    active_ts                      = "1",
    first_label_start              = multivalue_17_handle,
    enable_second_label            = "1",
    second_label_start             = "5000",
    label_mode                     = "fixed",
    cmac                           = "1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_route_config', _result_)

print "Configuration complete in port 1...\n"

############################################################################

#Creating OSPF Stack on top of ipv4 2 stack
print "Creating OSPF Stack on top of ipv4 2 stack\n"
_result_ = ixiangpf.emulation_ospf_config(
      handle                                                    = ipv4_2_handle,
      router_interface_active                                   = "1",
      protocol_name                                             = """OSPFv2-IF 2""",
      router_active                                             = "1",
      network_type                                              = "ptop",
      router_id                                                 = "194.0.0.1",
      mode                                                      = "create",
)

if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_ospf_config', _result_)

ospfv2_2_handle = _result_['ospfv2_handle']
 
#Adding IPv4 Prefix Pools behind first DG in Port2
print "Adding IPv4 Prefix Pools behind first DG in Port2\n"
_result_ = ixiangpf.multivalue_config (
    pattern                = "counter",
    counter_start          = "3.2.2.2",
    counter_step           = "0.0.0.1",
    counter_direction      = "increment",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_20_handle = _result_['multivalue_handle']

_result_ = ixiangpf.network_group_config(
      protocol_handle                       = deviceGroup_4_handle,
      protocol_name                         = """PE Loopback Address Pool 2""",
      multiplier                            = "1",
      enable_device                         = "1",
      connected_to_handle                   = ethernet_2_handle,
      type                                  = "ipv4-prefix",
      ipv4_prefix_network_address           = multivalue_20_handle,
      ipv4_prefix_length                    = "32",
      ipv4_prefix_multiplier                = "2",
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('network_group_config', _result_)   

ipv4PrefixPools_2_handle = _result_['ipv4_prefix_pools_handle']
networkGroup_2_handle = _result_['network_group_handle'] 

# Configuring OSPF Prefix Pool Parameters in Port2
print "Configuring OSPF Prefix Pool Parameters in Port2\n"
_result_ = ixiangpf.emulation_ospf_network_group_config(
      handle                           = networkGroup_2_handle,
      mode                             = "modify",
      ipv4_prefix_metric               = "0",
      ipv4_prefix_active               = "1",
      ipv4_prefix_route_origin         = "another_area",
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_ospf_network_group_config', _result_)

# Add VTEP 2 behind IPv4 Prefix Pool 2
print "Add VTEP 2 behind IPv4 Prefix Pool 2\n"
_result_ = ixiangpf.topology_config(
      device_group_name            = """VTEP 2""",
      device_group_multiplier      = "2",
      device_group_enabled         = "1",
      device_group_handle          = networkGroup_2_handle,
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('topology_config', _result_)

deviceGroup_4_handle = _result_['device_group_handle']

_result_ = ixiangpf.multivalue_config(
      pattern                = "counter",
      counter_start          = "3.2.2.2",
      counter_step           = "0.0.0.1",
      counter_direction      = "increment",
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_15_handle = _result_['multivalue_handle']

# Add ipv4 loopback in DG2
print "Add ipv4 loopback in DG2\n";
_result_ = ixiangpf.interface_config(
      protocol_name            = """IPv4 Loopback 2""",
      protocol_handle          = deviceGroup_4_handle,
      enable_loopback          = "1",
      connected_to_handle      = networkGroup_2_handle,
      intf_ip_addr             = multivalue_15_handle,
      netmask                  = "255.255.255.255",
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('interface_config', _result_)

ipv4Loopback_2_handle = _result_['ipv4_loopback_handle']

# Adding BGP peer over ipv4 Loopback
print "Adding BGP peer over ipv4 Loopback\n";

_result_ = ixiangpf.multivalue_config (
    pattern                = "counter",
    counter_start          = "a1:01:02:00:00:01",
    counter_step           = "00:00:00:00:00:01",
    counter_direction      = "increment",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_22_handle = _result_['multivalue_handle']

_result_ = ixiangpf.multivalue_config (
    pattern                = "counter",
    counter_start          = "2.2.2.2",
    counter_step           = "0.0.0.1",
    counter_direction      = "increment",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_23_handle = _result_['multivalue_handle']

_result_ = ixiangpf.emulation_bgp_config(
      mode                              = "enable",
      active                            = "1",
      handle                            = ipv4Loopback_2_handle,
      ip_version                        = "4",
      remote_ip_addr                    = multivalue_23_handle,
      count                             = "1",
      local_router_id                   = "3.2.2.2",
      ethernet_segments_count           = "1",
      filter_evpn                       = "1",
      evpn                              = "1",
      operational_model                 = "symmetric",
      routers_mac_or_irb_mac_address    = multivalue_22_handle,
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_config', _result_)

bgpIpv4Peer_2_handle = _result_['bgp_handle']

# Add EVPN-VxLAN stack on top of BGP
print "Add EVPN-VxLAN stack on top of BGP\n"
_result_ = ixiangpf.emulation_bgp_route_config(
      handle      = bgpIpv4Peer_2_handle,
      mode        = "create",
      evpn_vxlan  = "1",
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_route_config', _result_)

bgpIPv4EvpnVXLAN_3_handle = _result_['evpn_evi']

# Configure BGP Ethernet Segment stack
print "Configure BGP Ethernet Segment stack\n"
_result_ = ixiangpf.emulation_bgp_config(
      mode                                               = "modify",
      handle                                             = bgpIpv4Peer_2_handle,
      active_ethernet_segment                            = "1",
      esi_type                                           = "type0",
      esi_value                                          = "2",
      include_mac_mobility_extended_community            = "0",
      support_multihomed_es_auto_discovery               = "1",
      auto_configure_es_import                           = "1",
      support_fast_convergence                           = "1",
      enable_single_active                               = "0",
      advertise_inclusive_multicast_route                = "1",
      evis_count                                         = "2",
      ethernet_segment_name                              = """BGP Ethernet Segment 4""",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_config', _result_)

# Configure EVI parameters in port2

# Adding multivalue_29 to configure -ad_route_labels
_result_ = ixiangpf.multivalue_config (
    pattern                = "counter",
    counter_start          = "1001",
    counter_step           = "1",
    counter_direction      = "increment",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_29_handle = _result_['multivalue_handle']

# Adding multivalue_30 to configure -upstream_downstream_assigned_mpls_label
_result_ = ixiangpf.multivalue_config (
    pattern                = "counter",
    counter_start          = "2001",
    counter_step           = "1",
    counter_direction      = "increment",
)
multivalue_30_handle = _result_['multivalue_handle']

if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_30_handle = _result_['multivalue_handle']

print "Configure EVI parameters in Port2\n"
_result_ = ixiangpf.emulation_bgp_route_config(
      handle                                           = bgpIpv4Peer_2_handle,
      mode                                             = "modify",
      ad_route_label                                   = multivalue_29_handle,
      upstream_downstream_assigned_mpls_label          = multivalue_30_handle,
      evpn_vxlan                                       = "1",
      no_of_mac_pools                                  = "1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_route_config', _result_)

# Create MAC/IP Pool behind PE Router 1
print "Create MAC/IP Pool behind PE Router 1\n"

_result_ = ixiangpf.multivalue_config (
    pattern                = "counter",
    counter_start          = "42.22.22.22.22.22",
    counter_step           = "00.00.00.01.00.00",
    counter_direction      = "increment",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_36_handle = _result_['multivalue_handle']

_result_ = ixiangpf.network_group_config(
      protocol_handle                       = deviceGroup_4_handle,
      protocol_name                         = "Hosts_2",
      multiplier                            = "1",
      enable_device                         = "1",
      connected_to_handle                   = bgpIPv4EvpnVXLAN_3_handle,
      type                                  = "mac-ipv4-prefix",
      mac_pools_multiplier                  = "5",
      mac_pools_prefix_length               = "48",
      mac_pools_mac                         = multivalue_36_handle,
      ipv4_prefix_network_address           = "215.1.0.1",
      ipv4_prefix_network_address_step      = "0.1.0.0",
      ipv4_prefix_length                    = "32",
   )
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('network_group_config', _result_)

macPools_2_handle = _result_['mac_pools_handle']
ipv4PrefixPools_4_handle = _result_['ipv4_prefix_pools_handle']
networkGroup_9_handle = _result_['network_group_handle']

# Configure BGP properties in MAC Pool
print "Configure BGP properties in MAC Pool\n"

_result_ = ixiangpf.multivalue_config (
    pattern                = "counter",
    counter_start          = "5501",
    counter_step           = "1",
    counter_direction      = "increment",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('multivalue_config', _result_)

multivalue_37_handle = _result_['multivalue_handle']

_result_ = ixiangpf.emulation_bgp_route_config(
      handle                                          = networkGroup_9_handle,
      mode                                            = "create",
      active                                          = "1",
      max_route_ranges                                = "1",
      label_step                                      = "1",
      advertise_ipv4_address                          = "1",
      active_ts                                       = "1",
      first_label_start                               = multivalue_37_handle,
      enable_second_label                             = "1",
      second_label_start                              = "6000",
      label_mode                                      = "fixed",
      cmac                                            = "1",
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_route_config', _result_)

print "Configuration complete in port 2...\n"

############################################################################
# Start All protocols                                                      #
############################################################################    
print ('Starting all protocol(s) ...')
   
_result_ = ixiangpf.test_control(action='start_all_protocols')
# Check status
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('ixiangpf.test_control', _result_)
time.sleep(60)

############################################################################
# Retrieve protocol statistics                                             #
############################################################################
print ('Fetching BGP aggregated statistics')               
protostats = ixiangpf.emulation_bgp_info(\
        handle = bgpIpv4Peer_1_handle,
        mode   = 'stats')
if protostats['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_info', protostats)

#pprint(protostats)
print(protostats)

############################################################################
# Retrieve protocol learned info                                           #
############################################################################
print "Fetching EVPN  learned info\n"
# Check Learned Info for port 2 using BGP Router handle
print "Check Learned Info using BGP Router handle ...\n"
linfostatus = ixiangpf.emulation_bgp_info(
        handle = bgpIpv4Peer_1_handle,
        mode   = 'learned_info')
if linfostatus['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_info', linfostatus)

print('Fetched Linfo successfully...')

print("All learned info -----------------------")
print(linfostatus)
print("----------------------------------------")	

############################################################################
# On The Fly disable/enable C-MAC
############################################################################
print "On The Fly disable C-MAC\n";
#(handle : user needs to create and provide handle for cMacProperties, as scriptgen does not return this handle by default)
disable_cmac = ixiangpf.emulation_bgp_route_config (
   handle    = '/topology:1/deviceGroup:1/networkGroup:1/deviceGroup:1/networkGroup:1/macPools:1/cMacProperties:3',
   mode      = 'disable')

if disable_cmac['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_route_config', disable_cmac)

print "Apply On The Fly changes\n";
applyChanges = ixiangpf.test_control (
   action = 'apply_on_the_fly_changes')

time.sleep(10)

print "On The Fly enable C-MAC\n";
#(handle : user needs to create and provide handle for cMacProperties, as scriptgen does not return this handle by default)
enable_cmac = ixiangpf.emulation_bgp_route_config (
   handle    = '/topology:1/deviceGroup:1/networkGroup:1/deviceGroup:1/networkGroup:1/macPools:1/cMacProperties:3',
   mode      = 'enable')

if enable_cmac['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('emulation_bgp_route_config', enable_cmac)

print "Apply On The Fly changes\n";
applyChanges = ixiangpf.test_control (
   action = 'apply_on_the_fly_changes')

time.sleep(30)

################################################################################
# Configure_L2_L3_IPv4 traffic                                                 #
################################################################################
print ('Configuring L2-L3 IPv4 traffic item ...')
# Check status

print "Configuring L2-L3 Ethernet Traffic item ...\n"
_result_ = ixiangpf.traffic_config (
    mode                    =        'create',
    traffic_generator       =        'ixnetwork_540',
    endpointset_count       =        '1',
    emulation_src_handle    =        [[networkGroup_4_handle]],
    emulation_dst_handle    =        [[networkGroup_9_handle]],
    name                    =        'Ethernet_Traffic',
    circuit_endpoint_type   =        'ethernet_vlan',
    rate_pps                =        '100',
    track_by                =        'trackingenabled0 mplsFlowDescriptor0',
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('traffic_config', _result_)

print "Configured L2-L3 Ethernet traffic item!!!\n"

_result_ = ixiangpf.traffic_config(
    mode                               = 'create',
    traffic_generator                  = 'ixnetwork_540',
    endpointset_count                  = 1,
    emulation_src_handle               = [[networkGroup_4_handle]],
    emulation_dst_handle               = [[networkGroup_9_handle]],
    name                               = 'IPv4_Traffic',
    circuit_endpoint_type              = 'ipv4',
    frame_size                         = '512',
    rate_pps                           = '1000',
    track_by                           = 'trackingenabled0 ipv4DestIp0',
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('traffic_config', _result_)
    
config_elements = ixiatcl.convert_tcl_list(_result_['traffic_item'])
current_config_element = config_elements[0]
    
print ('Configured L2-L3 IPv4 traffic item!!!')

############################################################################
#  Start L2-L3 traffic configured earlier                                  #
############################################################################
print ('Running Traffic...')
_result_ = ixiangpf.traffic_control(
        action='run',
        traffic_generator='ixnetwork_540',
        type='l23'
)

if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('traffic_control', _result_)

print ('Let the traffic run for 30 seconds ...')
time.sleep(30)

############################################################################
# Retrieve L2-L3 traffic stats                                             #
############################################################################
print ('Retrieving L2-L3 traffic stats')
trafficStats = ixiangpf.traffic_stats(
        mode                 = 'all',
        traffic_generator       = 'ixnetwork_540',
        measure_mode          = 'mixed'
)
if trafficStats['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('traffic_stats', trafficStats)

print(trafficStats)

############################################################################
# Stop L2-L3 traffic started earlier                                       #
############################################################################
print ('Stopping Traffic...')
_result_ = ixiangpf.traffic_control(
        action             ='stop',
        traffic_generator  ='ixnetwork_540',
        type               ='l23',
)
if _result_['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('traffic_control', _result_)

time.sleep(5)
    
############################################################################
# Stop all protocols                                                       #
############################################################################
print ('Stopping all protocol(s) ...')
stop = ixiangpf.test_control(action='stop_all_protocols')
                  
if stop['status'] != IxiaHlt.SUCCESS:
    ErrorHandler('test_control', stop)

print ('!!! Test Script Ends !!!')
