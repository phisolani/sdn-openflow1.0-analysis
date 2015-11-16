#!/bin/bash

# kill the controller
# sudo killall java

# start the controller
# sh init_controller.sh

# start the experiment
# sudo python im_2015_experiment.py --period=10 --monitor=300 --ip='143.54.12.122' --type='flow' --topology='tree' --depth=3 --fanout=2
# sudo python im_2015_experiment.py --period=5 --monitor=300 --ip='143.54.12.122' --type='flow' --topology='single' --hosts=8

python config_controller.py 1
sh init_controller.sh &
sleep 10
sudo python dissertation_preliminary_experiment.py \--period=5 \--monitor=300 \--ip='192.168.122.210' \--type='flow' \--topology='single' \--idle=5 \--hosts=4
sudo killall java
sudo mn -c

python config_controller.py 1
sh init_controller.sh &
sleep 10
sudo python dissertation_preliminary_experiment.py \--period=5 \--monitor=300 \--ip='192.168.122.210' \--type='flow' \--topology='single' \--idle=5 \--hosts=4
sudo killall java
sudo mn -c
#gnuplot ../results/plot.gnu
