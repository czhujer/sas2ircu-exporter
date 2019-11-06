#!/usr/bin/python
# coding=utf-8
#
# Author: Patrik Majer <patrik.majer.pisek@gmail.com>
# Date (last updated): 2019-10-21
#
# based of this nrpe check
#
# https://github.com/leibler/check_mk-sas2ircu/blob/master/agents/plugins/sas2ircu
#
# Original Author: Leo Eibler <le@sprossenwanne.at>
# Original Date (last updated): 2014-01-09
#
# This is a check for sas2ircu RAID disks (used in Dell R200, R210, R210II Servers)
# the commandline tool 'sas2ircu' has to be installed.
#
# place this file in the plugins directory of the check_mk agent
#
# to use this check on debian 7 x64 download the sas2ircu utility debian package from:
#   http://hwraid.le-vert.net/debian/pool-wheezy/sas2ircu_16.00.00.00-1_amd64.deb
# install the package:
#   dpkg -i sas2ircu_16.00.00.00-1_amd64.deb
# test the utility:
#   sas2ircu 0 display
#
#
# example output of this check:
#   <<<sas2ircu>>>
#   volume 0 79 okay_(oky) 0d9383a8258e32ac raid1 1907200
#   disk 0 0 optimal_(opt) 5000c50-0-569e-8a83 seagate st2000nm0023 z1x065wj sas sas_hdd
#   disk 0 1 optimal_(opt) 5000c50-0-569f-2021 seagate st2000nm0023 z1x0j231 sas sas_hdd
#
# each line starts with the type ('disk' or 'volume')
# the 2nd column is the controller id (first controller=0, second controller=1, ...)
# the 3rd column for volume is the volume id and for disks is the slot number
# the 4th column is the state
# the order of the fields is configured in the arrays 'volumeOutputOrder' and 'diskOutputOrder'
#
# Integrated RAID Volume State values are as follows:
# Okay (OKY) – The volume is active and drives are functioning properly. User data is protected if the current RAID level provides data protection.
# Degraded (DGD) – The volume is active. User data is not fully protected because the configuration has changed or a drive has failed.
# Failed (FLD) – The volume has failed.
# Missing (MIS) – The volume is missing.
# Initializing (INIT) – The volume is initializing.
# Online (ONL) – The volume is online.
# Physical device State values are as follows:
# Online (ONL) – The drive is operational and is part of a volume.
# Hot Spare (HSP) – The drive is a hot spare that is available to replace a failed drive in a volume.
# Ready (RDY) – The drive is ready for use as a normal disk drive, or it is ready to be assigned to a volume or a hot spare pool.
# Available (AVL) – The drive might not be ready, and it is not suitable for use in a volume or a hot spare pool.
# Failed (FLD) – The drive failed and is now offline.
# n Missing (MIS) – The drive has been removed or is not responding.
# Standby (SBY) – The device is not a hard-disk device.
# Out of Sync (OSY) – The drive, which is part of an Integrated RAID volume, is not in sync with other drives that are part of the volume.
# Degraded (DGD) – The drive is part of a volume and is in degraded state.
# Rebuilding (RBLD) – The drive is part of a volume and is currently rebuilding.
# Optimal (OPT) – The drive is optimal and is part of a volume.
# Physical device Drive Type values are as follows:
# SAS_HDD – The drive is a SAS HDD.
# SATA_HDD – The drive is a SATA HDD.
# SAS_SSD – The drive is a SAS SSD.
# SATA_SSD – The drive is a SATA SSD.
# Physical device Protocol values are as follows:
# SAS – The drive supports SAS protocol.
# SATA – The drive supports SATA protocol.
#
#  Copyright 2014 Leo Eibler (http://www.eibler.at)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import subprocess
import sys

# raidCommand is the cli utility name which is executed to get the information
raidCommand = "/root/sas2ircu"

# volumeAttrs is a list of key:value pairs where key is the volume fieldname of the output from sas2ircu cli utility and value is the internal name used in *OutputOrder list. use lower case letters!
volumeAttrs = {'volume id': 'volumeid', 'status of volume': 'status', 'volume wwid': 'wwid', 'raid level': 'raid',
               'size (in mb)': 'size'}
# diskAttrs is a list of key:value pairs where key is the disk fieldname of the output from sas2ircu cli utility and value is the internal name used in *OutputOrder list. use lower case letters!
diskAttrs = {'slot #': 'slot', 'state': 'status', 'sas address': 'sasaddr', 'manufacturer': 'manufacturer',
             'model number': 'model', 'serial no': 'serial', 'protocol': 'protocol', 'drive type': 'type'}

# volumeOutputOrder is a list of the internal names for volumes used for the output in the given order
# volumeOutputOrder = [ 'controller', 'volumeid', 'status', 'wwid', 'raid', 'size' ]
volumeOutputOrder = ['status', 'raid', 'size']

# diskOutputOrder is a list of the internal names for disks used for the output in the given order
# diskOutputOrder = ['status', 'sasaddr', 'manufacturer', 'model', 'serial', 'protocol', 'type']
diskOutputOrder = ['status', 'model', 'serial', 'protocol', 'type']


def returnVolumeTpl():
    volumeTpl = {'controller': '-1'}
    for name, code in volumeAttrs.items():
        volumeTpl[code] = '-'
    return volumeTpl


def returnDiskTpl():
    diskTpl = {'controller': '-1'}
    for name, code in diskAttrs.items():
        diskTpl[code] = '-'
    return diskTpl


# checkNextController is a flag if current controller (int 0-255) is present and so the next controller id should be checked
checkNextController = True
listVolumes = []
listDisks = []

for i in range(0, 255):
    if checkNextController:
        cmd = subprocess.Popen(raidCommand + " " + str(i) + " DISPLAY", shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        mode = "unknown"
        volumeNr = 0
        diskNr = 0
        volume = returnVolumeTpl()
        disk = returnDiskTpl()
        for line in cmd.stdout:
            line = line.strip().lower()
            if "sas2ircu: not found" in line:
                checkNextController = False
                break
            checkIfPresentLine = "SAS2IRCU: No Controller Found at index " + str(i) + "."
            checkIfPresentLine = checkIfPresentLine.lower()
            if line == checkIfPresentLine:
                checkNextController = False
                break
            parts = map(str.strip, line.split(":"))
            if parts[0] == "sas2ircu" or parts[0].startswith("------") or parts[0].startswith("ir volume") or len(
                    parts[0]) == 0:
                if mode == "volume":
                    if volume['controller'] != "-1":
                        listVolumes.append(volume)
                        volume = returnVolumeTpl()
                if mode == "harddisk":
                    if disk['controller'] != "-1":
                        listDisks.append(disk)
                        disk = returnDiskTpl()
            if parts[0] == "volume id":
                volume['controller'] = str(i)
                volume['volume'] = parts[1]
                mode = "volume"
            if parts[0] == "device is a hard disk":
                disk['controller'] = str(i)
                mode = "harddisk"
            if mode == "volume" and len(parts) > 1:
                if parts[0] in volumeAttrs:
                    volume[volumeAttrs[parts[0]]] = parts[1].replace(" ", "_")
            if mode == "harddisk" and len(parts) > 1:
                if parts[0] in diskAttrs:
                    disk[diskAttrs[parts[0]]] = parts[1].replace(" ", "_")
    else:
        break

# output the checks in order of volumeOutputOrder and diskOutputOrder

metrics = {}

for volume in listVolumes:
    metric_name_prefix = "node_sas2ircu_volume"
    first_label = "id=\"" + volume['controller'] + "_" + volume['volumeid'] + "\""

    labels = ""
    for name in volumeOutputOrder:
        if name == "raid":
            metric_value = volume[name].replace('raid', '')
        else:
            metric_value = volume[name]

        if name == "status":
            metric_name = metric_name_prefix + "_" + name + "_ok"
            if metric_value == 'okay_(oky)':
                metric_value = "1"
            else:
                metric_value = "0"
        else:
            metric_name = metric_name_prefix + "_" + name

        key = metric_name + "_" + volume['controller'] + "_" + volume['volumeid']

        metrics[key] = {}
        metrics[key]['name'] = metric_name
        metrics[key]['first_label'] = first_label
        metrics[key]['value'] = metric_value

for disk in listDisks:
    metric_name_prefix = "node_sas2ircu_disk"
    first_label = "id=\"" + disk['controller'] + "_" + disk['slot'] + "\""

    labels = ",model=\"" + disk['model'] + "\""
    labels = labels + ",serial=\"" + disk['serial'] + "\""

    for name in diskOutputOrder:
        if name == "model" or name == "serial":
            break
        if name == "status":
            metric_name = metric_name_prefix + "_" + name + "_ok"
            if disk[name] == "optimal_(opt)":
                disk[name] = "1"
            else:
                disk[name] = "0"
        else:
            metric_name = metric_name_prefix + "_" + name

        key = metric_name + "_" + disk['controller'] + "_" + disk['slot']

        metrics[key] = {}
        metrics[key]['name'] = metric_name
        metrics[key]['first_label'] = first_label
        metrics[key]['labels'] = labels
        metrics[key]['value'] = disk[name]

for key, params in sorted(metrics.iteritems()):
    first_label = ""
    labels = ""
    for param, value in params.iteritems():
        if param == "first_label":
            first_label = value
        if param == "labels":
            labels = metrics[key]['labels']

    print metrics[key]['name'] + "{" + first_label + labels + "}" + " " + metrics[key]['value']

sys.stdout.flush()
