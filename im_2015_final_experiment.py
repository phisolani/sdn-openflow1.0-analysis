#!/usr/bin/python
"""
Create a network where different switches are connected to
different controllers, by creating a custom Switch() subclass.
"""

from mininet.net import Mininet
from mininet.node import OVSSwitch, Controller, RemoteController, Host
from mininet.topo import SingleSwitchTopo
from mininet.topolib import TreeTopo
from mininet.log import setLogLevel
from mininet.log import info
from mininet.cli import CLI
from mininet.util import custom, customConstructor
from mininet.link import Link, TCLink
from topologies.ufrgstopo import UFRGSTopo
from optparse import OptionParser
import time
import sys
import urllib, json
import commands
import os
import pprint
import shutil
import subprocess
import requests

# Parameters from shell
parser = OptionParser()
parser.add_option("","--period",type="int",default=1)
parser.add_option("","--monitor",type="int",default=30)
parser.add_option("","--ip",type="string",default="10.1.1.121")
parser.add_option("","--type",type="string",default="flow")
parser.add_option("","--topology",type="string",default="tree")
parser.add_option("","--hosts",type="int",default=8)
parser.add_option("","--depth",type="int",default=3)
parser.add_option("","--fanout",type="int",default=2)
parser.add_option("","--idle",type="int",default=5)

(options, args) = parser.parse_args()
print options

experiment_path = '../results/' + options.topology + '_' + str(options.period) + '_' + str(options.monitor) + '_' + options.type + '_' + str(options.idle) + '_' +  str(time.time()) + '/'
os.mkdir(experiment_path)
os.chown(experiment_path, 1000, 1000)

# Verifing topology type
if options.topology == 'tree':
  topo = TreeTopo( depth=options.depth, fanout=options.fanout )
elif options.topology == 'single':
  topo = SingleSwitchTopo( k=options.hosts )
elif options.topology == 'ufrgs':
  topo = UFRGSTopo()

# Setting mininet configuration
setLogLevel( 'info' )

# Setting links configuration
LINKS = {'default':Link, 'tc':TCLink}
link = customConstructor( LINKS, 'tc,bw=100' )

# Adding root host
root = Host( 'root', inNamespace=False )

# Adding the remote controller
net = Mininet( topo=topo, link=link, autoSetMacs=True, controller=lambda name: RemoteController( name, ip=options.ip ) )

for host in net.hosts:
   host.linkTo ( root )

# Start the network
net.start()

# Waiting for apache starts
file_server = 0
video_server = 1

net.hosts[file_server].cmd('service apache2 restart')
net.hosts[video_server].cmd('su - pedro -c \'vlc -vvv /var/www/chulapa.mp4 --sout "#standard{access=http,mux=asf,dst=:8080}"\' &')
#net.hotst[controller].cmd('sh init_controller.sh')
time.sleep( 10 )

# Hosts requesting the file 
for i in range(0, int(len(net.hosts))):
   if i != 0 and i != 1:
      if (i % 7) == 0:
         net.hosts[i].cmd('./video_request.py ' + str(video_server + 1) + ' &')
      else:
         net.hosts[i].cmd('./file_request.py ' + str(file_server + 1) + ' &') 

# Setting monitor url and results files 
url = 'http://' + options.ip + ':8080/wm/core/switch/all/' + options.type + '/json'
results_filename = 'results_file_' + options.topology + '_' + str(options.period) + '_' + str(options.monitor) + '_' + options.type + '_' + str(options.idle)
results_file = open(experiment_path + results_filename, "w")
results_file.write(
   # Overall
   'avgResp ' \
   + 'tReq ' \
   + 'tRep ' \
   # Controller-to-switch
   + 'readReqPC ' \
   + 'readReqPL ' \
   + 'readRepPC ' \
   + 'readRepPL ' \
   + 'barReqPC ' \
   + 'barReqPL ' \
   + 'barRepPC ' \
   + 'barRepPL ' \
   + 'sendPC ' \
   + 'sendPL ' \
   + 'modPC ' \
   + 'modPL ' \
   + 'featRepPC ' \
   + 'featRepPL ' \
   + 'confReqPC ' \
   + 'confReqPL ' \
   + 'confRepPC ' \
   + 'confRepPL ' \
   # Asynchronous
   + 'packInPC ' \
   + 'packInPL ' \
   + 'flRemPC ' \
   + 'flRemPL ' \
   + 'pStaPC ' \
   + 'pStaPL ' \
   + 'erroPC ' \
   + 'erroPL ' \
   # Symmetric
   + 'hellReqPC ' \
   + 'hellReqPL ' \
   + 'hellRepPC ' \
   + 'hellRepPL ' \
   + 'echoReqPC ' \
   + 'echoReqPL ' \
   + 'echoRepPC ' \
   + 'echoRepPL ' \
   + 'vendReqPC ' \
   + 'vendReqPL ' \
   + 'vendRepPC ' \
   + 'vendRepPL ' \
   # Other messages
   + 'otheReqPC ' \
   + 'otheReqPL ' \
   + 'otheRepPC ' \
   + 'otheRepPL ' \
   # New information
   + 'flowCount ' \
   + 'flowIdleCount' + '\n')

# For each monitor do
old_data = {}
for i in range(0, options.monitor):
   if i == 120:
      payload = {'idle_timeout': 60,'hard_timeout': 0}
      requests.get("http://localhost:8080/wm/core/controller/configure/json", data=payload)
   if i == 240:
      payload = {'idle_timeout': 30,'hard_timeout': 0}
      requests.get("http://localhost:8080/wm/core/controller/configure/json", data=payload) 
   if i < 360:
      time.sleep( 5 )
   else: 
      if i < 375:
         time.sleep( 40 )
      else:
         if i < 395:
            time.sleep( 30 )
         else:
            time.sleep( 15 )
   #time.sleep( options.period )
   response = urllib.urlopen(url)
   data = json.loads(response.read())
   # Counting the idle flows
   f_idle_counter = 0
   f_counter = 0
   for switch_dpid in data:
       if switch_dpid == 'Aggregate Statistics':
           continue
       elif switch_dpid in old_data:
           for flow in data[switch_dpid]:
               for old_flow in old_data[switch_dpid]:
                   if flow['match'] == old_flow['match'] and flow['packetCount'] == old_flow['packetCount']: 
                       f_idle_counter += 1
       f_counter += len(data[switch_dpid])
   old_data = data
   results_file.write(
   # Overall
   str(data['Aggregate Statistics']['avgResponse']) + ' ' \
   + str(data['Aggregate Statistics']['timeRequest']) + ' ' \
   + str(data['Aggregate Statistics']['timeReply']) + ' ' \
   # Controller-to-switch
   + str(data['Aggregate Statistics']['readStateRequestCount']) + ' ' \
   + str(data['Aggregate Statistics']['readStateRequestLength']) + ' ' \
   + str(data['Aggregate Statistics']['readStateReplyCount']) + ' ' \
   + str(data['Aggregate Statistics']['readStateReplyLength']) + ' ' \
   + str(data['Aggregate Statistics']['barrierRequestCount']) + ' ' \
   + str(data['Aggregate Statistics']['barrierRequestLength']) + ' ' \
   + str(data['Aggregate Statistics']['barrierReplyCount']) + ' ' \
   + str(data['Aggregate Statistics']['barrierReplyLength']) + ' ' \
   + str(data['Aggregate Statistics']['sendPacketCount']) + ' ' \
   + str(data['Aggregate Statistics']['sendPacketLength']) + ' ' \
   + str(data['Aggregate Statistics']['modifyStateCount']) + ' ' \
   + str(data['Aggregate Statistics']['modifyStateLength']) + ' ' \
   + str(data['Aggregate Statistics']['featuresReplyCount']) + ' ' \
   + str(data['Aggregate Statistics']['featuresReplyLength']) + ' ' \
   + str(data['Aggregate Statistics']['configurationRequestCount']) + ' ' \
   + str(data['Aggregate Statistics']['configurationRequestLength']) + ' ' \
   + str(data['Aggregate Statistics']['configurationReplyCount']) + ' ' \
   + str(data['Aggregate Statistics']['configurationReplyLength']) + ' ' \
   # Asynchronous
   + str(data['Aggregate Statistics']['packetInCount']) + ' ' \
   + str(data['Aggregate Statistics']['packetInLength']) + ' ' \
   + str(data['Aggregate Statistics']['flowRemovedCount']) + ' ' \
   + str(data['Aggregate Statistics']['flowRemovedLength']) + ' ' \
   + str(data['Aggregate Statistics']['portStatusCount']) + ' ' \
   + str(data['Aggregate Statistics']['portStatusLength']) + ' ' \
   + str(data['Aggregate Statistics']['errorCount']) + ' ' \
   + str(data['Aggregate Statistics']['errorLength']) + ' ' \
   # Symmetric
   + str(data['Aggregate Statistics']['helloRequestCount']) + ' ' \
   + str(data['Aggregate Statistics']['helloRequestLength']) + ' ' \
   + str(data['Aggregate Statistics']['helloReplyCount']) + ' ' \
   + str(data['Aggregate Statistics']['helloReplyLength']) + ' ' \
   + str(data['Aggregate Statistics']['echoRequestCount']) + ' ' \
   + str(data['Aggregate Statistics']['echoRequestLength']) + ' ' \
   + str(data['Aggregate Statistics']['echoReplyCount']) + ' ' \
   + str(data['Aggregate Statistics']['echoReplyLength']) + ' ' \
   + str(data['Aggregate Statistics']['vendorRequestCount']) + ' ' \
   + str(data['Aggregate Statistics']['vendorRequestLength']) + ' ' \
   + str(data['Aggregate Statistics']['vendorReplyCount']) + ' ' \
   + str(data['Aggregate Statistics']['vendorReplyLength']) + ' ' \
   # Other messages
   + str(data['Aggregate Statistics']['otherRequestCount']) + ' ' \
   + str(data['Aggregate Statistics']['otherRequestLength']) + ' ' \
   + str(data['Aggregate Statistics']['otherReplyCount']) + ' ' \
   + str(data['Aggregate Statistics']['otherReplyLength']) + ' ' \
   # Net information
   + str(f_counter) + ' ' \
   + str(f_idle_counter) + '\n')
   
results_file.close()
os.chown(experiment_path + results_filename, 1000, 1000)
# CLI( net )
# Kill proccesses before ending script
net.hosts[0].cmd("kill `ps ax | grep file_request | grep -v grep | awk '{print $1}'`")
net.hosts[0].cmd("kill `ps ax | grep video_request | grep -v grep | awk '{print $1}'`")
net.hosts[0].cmd("killall wget")
net.hosts[0].cmd("killall vlc")
net.stop()

results_file = open(experiment_path + results_filename,"r")
conteudo = results_file.readlines()

compiled_file = open(experiment_path + 'compiled_' + results_filename, "w")
compiled_file.write(
    # Overall
    'timeElapsed ' \
    + 'avgResp ' \
    + 'respTime ' \
    + 'readReqPC ' \
    + 'readReqPL ' \
    + 'readRepPC ' \
    + 'readRepPL ' \
    + 'packInPC ' \
    + 'packInPL ' \
    + 'sendPC ' \
    + 'sendPL ' \
    + 'modPC ' \
    + 'modPL ' \
    + 'otheReqPC ' \
    + 'otheReqPL ' \
    + 'otheRepPC ' \
    + 'otheRepPL ' \
    + 'packInRatio ' \
    + 'sendRatio ' \
    + 'modRatio ' \
    + 'otheReqRatio ' \
    + 'otheRepRatio ' \
    + 'flowCount ' \
    + 'flowIdleCount ' + '\n')

list_fields = []
results_fields = {}
t_elapsed = 0
first_t_rep = 0
for i in range(len(conteudo)):
    values = conteudo[i].strip().split(' ')
    list_values = []
    if i == 0:
        fields = conteudo[i].strip().split(' ')
        for j in fields:
            list_fields.append(j)
            results_fields[j] = 0
    elif i == 1:
        fields = conteudo[i].strip().split(' ')
        for j in fields:
            list_values.append(j)
        for j in range(len(list_fields)):
            results_fields[list_fields[j]] = list_values[j]
        first_t_rep = results_fields['tRep']
        compiled_file.write(
        # timeElapsed
        str(t_elapsed) + ' ' \
        # avgResp
        + results_fields['avgResp'] + ' ' \
        # respTime
        + str(int(results_fields['tReq'])-int(results_fields['tRep'])) + ' ' \
        # readReqPC
        + results_fields['readReqPC'] + ' ' \
        # readReqPL
        + results_fields['readReqPL'] + ' ' \
        # readRepPC
        + results_fields['readRepPC'] + ' ' \
        # readRepPL
        + results_fields['readRepPL'] + ' ' \
        # packInPC
        + results_fields['packInPC'] + ' ' \
        # packInPL
        + results_fields['packInPL'] + ' ' \
        # sendPC
        + results_fields['sendPC'] + ' ' \
        # sendPL
        + results_fields['sendPL'] + ' ' \
        # modPC
        + results_fields['modPC'] + ' ' \
        # modPL
        + results_fields['modPL'] + ' ' \
        # otheReqPC
        + results_fields['otheReqPC'] + ' ' \
        # otheReqPL
        + results_fields['otheReqPL'] + ' ' \
        # otheRepPC
        + results_fields['otheRepPC'] + ' ' \
        # otheRepPL
        + results_fields['otheRepPL'] + ' ' \
        # packInRatio
        + '0 ' \
        # sendRatio
        + '0 ' \
        # modRatio
        + '0 ' \
        # otheReqRatio
        + '0 ' \
        # otheRepRatio
        + '0 ' \
        # flowCount
        + results_fields['flowCount'] + ' ' \
        # flowIdleCount
        + results_fields['flowIdleCount'] + '\n')
    elif i > 1:
        old_results_fields = {}
        old_list_values = []
        old_fields = conteudo[i-1].strip().split(' ')
        for j in old_fields:
            old_list_values.append(j)
        for j in values:
            list_values.append(j)
        for j in range(len(list_fields)):
            results_fields[list_fields[j]] = list_values[j]
            old_results_fields[list_fields[j]] = old_list_values[j]
        
        #print('****')
        #print(results_fields['packInPL'])
        #print(old_results_fields['packInPL'])
        #print(int(results_fields['tRep']))
        #print(int(old_results_fields['tRep'])) 
        #print(int(results_fields['packInPL'])-int(old_results_fields['packInPL']))*8
        interval = (int(results_fields['tRep'])-int(old_results_fields['tRep']))/1000.0
        #print(interval)
        #print('----')
        t_elapsed = (int(results_fields['tRep'])-int(first_t_rep))/float(1000)
        compiled_file.write(
        # timeElapsed
        str(t_elapsed) + ' ' \
        # avgResp
        + results_fields['avgResp'] + ' ' \
        # respTime
        + str(int(results_fields['tReq'])-int(old_results_fields['tRep'])) + ' ' \
        # readReqPC
        + str(int(results_fields['readReqPC'])-int(old_results_fields['readReqPC'])) + ' ' \
        # readReqPL
        + str(int(results_fields['readReqPL'])-int(old_results_fields['readReqPL'])) + ' ' \
        # readRepPC
        + str(int(results_fields['readRepPC'])-int(old_results_fields['readRepPC'])) + ' ' \
        # readRepPL
        + str(int(results_fields['readRepPL'])-int(old_results_fields['readRepPL'])) + ' ' \
        # packInPC
        + str(int(results_fields['packInPC'])-int(old_results_fields['packInPC'])) + ' ' \
        # packInPL
        + str(int(results_fields['packInPL'])-int(old_results_fields['packInPL'])) + ' ' \
        # sendPC
        + str(int(results_fields['sendPC'])-int(old_results_fields['sendPC'])) + ' ' \
        # sendPL
        + str(int(results_fields['sendPL'])-int(old_results_fields['sendPL'])) + ' ' \
        # modPC
        + str(int(results_fields['modPC'])-int(old_results_fields['modPC'])) + ' ' \
        # modPL
        + str(int(results_fields['modPL'])-int(old_results_fields['modPL'])) + ' ' \
        # otheReqPC
        + str(int(results_fields['otheReqPC'])-int(old_results_fields['otheReqPC'])) + ' ' \
        # otheReqPL
        + str(int(results_fields['otheReqPL'])-int(old_results_fields['otheReqPL'])) + ' ' \
        # otheRepPC
        + str(int(results_fields['otheRepPC'])-int(old_results_fields['otheRepPC'])) + ' ' \
        # otheRepPL
        + str(int(results_fields['otheRepPL'])-int(old_results_fields['otheRepPL'])) + ' ' \
        # packInRatio
        + str((int(results_fields['packInPL'])-int(old_results_fields['packInPL']))*8/interval) + ' ' \
        # sendRatio
        + str((int(results_fields['sendPL'])-int(old_results_fields['sendPL']))*8/interval) + ' ' \
        # modRatio
        + str((int(results_fields['modPL'])-int(old_results_fields['modPL']))*8/interval) + ' ' \
        # otheReqRatio
        + str((int(results_fields['otheReqPL'])-int(old_results_fields['otheReqPL']))*8/interval) + ' ' \
        # otheRepRatio
        + str((int(results_fields['otheRepPL'])-int(old_results_fields['otheRepPL']))*8/interval) + ' ' \
        # flowCount
        + results_fields['flowCount'] + ' ' \
        # flowIdleCount
        + results_fields['flowIdleCount'] + '\n')
#print results_fields
compiled_file.close()
os.chown(experiment_path + 'compiled_' + results_filename, 1000, 1000)

## Data Graph
#plots = []
#for m in mapFlows:
#   plots.append('"./' + m + '" using 1:5 w l lw 4')
#graph_file = open(experiment_path + 'doGraphDataFlow.gp', "w")
#graph_file.write('set term pdfcairo enhanced dashed size 8,4 \n' \
#+ 'set output "acc_data_' + options.topology + '_' + str(options.period) + '_' + str(options.monitor) + '_' + options.type + '.pdf"\n' \
#+ 'set grid ytics \n' \
#+ 'set xlabel "Numero de monitoramentos" \n' \
#+ 'set ylabel "Tamanho (Bits)" \n' \
#+ 'set key outside bottom center box horizontal \n' \
#+ 'plot ' + ','.join(plots) + '\n')
#graph_file.close()
#os.chown(experiment_path + 'doGraphDataFlow.gp', 1000, 1000)
#
## Control Graph
#graph_file = open(experiment_path + 'doGraphControlFlow.gp', "w")
#graph_file.write('set term pdfcairo enhanced dashed size 8,4 \n' \
#+ 'set output "acc_control_' + options.topology + '_' + str(options.period) + '_' + str(options.monitor) + '_' + options.type + '.pdf"\n' \
#+ 'set grid ytics \n' \
#+ 'set xlabel "Numero de monitoramentos" \n' \
#+ 'set ylabel "Tamanho (Bits)" \n' \
#+ 'set key outside bottom center box horizontal \n' \
#+ 'plot "./compiled_' + results_filename + '" using 1:7 with lines lw 4, "./compiled_' + results_filename + '" using 1:8 with lines lw 4')
#graph_file.close()
#os.chown(experiment_path + 'doGraphControlFlow.gp', 1000, 1000)
#      
## ResponseTime Graph
#graph_file = open(experiment_path + 'doGraphResponseTimeFlow.gp', "w")
#graph_file.write('set term pdfcairo enhanced dashed size 8,4 \n' \
#+ 'set output "acc_response_time_' + options.topology + '_' + str(options.period) + '_' + str(options.monitor) + '_' + options.type + '.pdf"\n' \
#+ 'set grid ytics \n' \
#+ 'set xlabel "Numero de monitoramentos" \n' \
#+ 'set ylabel "Tamanho (Bits)" \n' \
#+ 'set key outside bottom center box horizontal \n' \
#+ 'plot "./compiled_' + results_filename + '" using 1:9 with lines lw 4')
#graph_file.close()
#os.chown(experiment_path + 'doGraphResponseTimeFlow.gp', 1000, 1000)
#
## COPY FILE
## shutil.copy2('groupFile.py', experiment_path)
#macs = {}
#for subdir, dirs, files in os.walk(experiment_path):
#   for f in files:
#      # print f
#      names = []
#      if f[0] == 's' and f[1] == '-':
#         names = f.replace('.dat', '').split('-')
#         src_dst = names[2] + '-' + names[3]
#         crr_file = open(experiment_path + f, "r")
#         content = crr_file.readlines()
#         for i in range(len(content)):
#            flow_time, duration_seconds, packet_count, byte_count, flow_rate = content[i].split(' ')
#            flow_time = float(flow_time)
#            duration_seconds = int(duration_seconds)
#            packet_count = int(packet_count)
#            byte_count = int(byte_count)
#            flow_rate = float(flow_rate)
#            if macs.has_key(src_dst):
#               if macs[src_dst].has_key(flow_time):
#                  macs[src_dst][flow_time][1] += duration_seconds
#                  macs[src_dst][flow_time][2] += packet_count
#                  macs[src_dst][flow_time][3] += byte_count
#                  macs[src_dst][flow_time][4] += flow_rate
#                  macs[src_dst][flow_time][5] += 1
#               else:
#                  macs[src_dst][flow_time] = [flow_time, duration_seconds, packet_count, byte_count, flow_rate, 1]
#            else:
#               macs[src_dst] = {flow_time: [flow_time, duration_seconds, packet_count, byte_count, flow_rate, 1]}
#
## print macs
#for m in macs:
#   crr_file = open(experiment_path + 'g-' + m + '.dat', "w")
#   for t in sorted(macs[m]):
#      crr_file.write(str(macs[m][t][0]) + ' ' \
#      + str(macs[m][t][1] / float(macs[m][t][5])) + ' ' \
#      + str(macs[m][t][2] / float(macs[m][t][5])) + ' ' \
#      + str(macs[m][t][3] / float(macs[m][t][5])) + ' ' \
#      + str(macs[m][t][4] / float(macs[m][t][5])) \
#      + '\n')
#   crr_file.close()
#   os.chown(experiment_path + 'g-' + m + '.dat', 1000, 1000)
#
## Group Flow Graph
#plots = []
#for m in macs:
#   plots.append('"./g-' + m + '.dat" using 1:5 w l lw 4')
#graph_file = open(experiment_path + 'doGraphGroupFlow.gp', "w")
#graph_file.write('set term pdfcairo enhanced dashed size 8,4 \n' \
#+ 'set output "acc_group_flow.pdf"\n' \
#+ 'set grid ytics \n' \
#+ 'set xlabel "Numero de monitoramentos" \n' \
#+ 'set ylabel "Tamanho (Bits)" \n' \
#+ 'set key outside bottom center box horizontal \n' \
#+ 'plot ' + ','.join(plots) + '\n')
#graph_file.close()
#os.chown(experiment_path + 'doGraphGroupFlow.gp', 1000, 1000)
#
## os.chown(experiment_path + 'groupFile.py', 1000, 1000)
## a = subprocess.Popen(['sudo', 'gnuplot', experiment_path + 'doGraphDataFlow.gp'])
## a.wait()
#
#plot_file = open(experiment_path + 'doPlots.sh', "w")
#plot_file.write('#!/usr/bin/bash \n' \
#+ '# List of plots \n' \
#+ 'gnuplot doGraphDataFlow.gp \n' \
#+ 'gnuplot doGraphControlFlow.gp \n' \
#+ 'gnuplot doGraphResponseTimeFlow.gp \n' \
#+ 'gnuplot doGraphGroupFlow.gp \n')
#plot_file.close()
#os.chown(experiment_path + 'doPlots.sh', 1000, 1000)
#
## a = subprocess.Popen(['sh', '/home/pedro/Documentos/phisolani' + experiment_path.replace('.','') + 'doPlots.sh'])
## a.wait()
