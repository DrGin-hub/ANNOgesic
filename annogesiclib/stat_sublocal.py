#!/usr/bin/python

import os	
import sys
import random
import csv
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from annogesiclib.gff3 import Gff3Parser
import numpy as np

def plot(subs, total, unknown, strain, prefix_name):
    nums = []
    nums_no_unknown = []
    classes = []
    classes_no_unknown = []
    width = 0.4
    for local, num in subs.items():
        if local == "Unknown":
            tmp_unknown = [local, num]
        else:
            nums.append(num)
            nums_no_unknown.append(num)
            classes.append(local)
            classes_no_unknown.append(local)
    nums.append(tmp_unknown[1])
    classes.append(tmp_unknown[0])
    fig = plt.figure(figsize=(12, 16))
    plt.subplot(211)
    ind = np.arange(len(nums))
    rects1 = plt.bar(ind, nums, width,  color='#FF9999')
    plt.title('Subcellular localization with Unknown\n', fontsize=16)
    plt.ylabel('Amount', fontsize=16)
    plt.xlim([0, len(nums) + 1])
    plt.xticks(ind+width, classes, rotation=40, fontsize=16, ha='right')
    plt.tight_layout(2, None, None, None)
    plt.subplot(212)
    ind = np.arange(len(nums_no_unknown))
    rects1 = plt.bar(ind, nums_no_unknown, width,  color='#FF9999')
    plt.title('Subcellular localization without Unknown\n', fontsize=16)
    plt.ylabel('Amount', fontsize=16)
    plt.xlim([0, len(nums_no_unknown) + 1])
    plt.xticks(ind+width, classes_no_unknown, rotation=40, fontsize=16, ha='right')
    plt.tight_layout(2, None, None, None)
    plt.savefig("_".join([prefix_name, strain + ".png"]))

def read_table(psortb_file, subs, total_nums, unknown_nums):
    pre_strain = ""
    fh = open(psortb_file, "r")
    for row in csv.reader(fh, delimiter="\t"):
        if pre_strain != row[0]:
            subs[row[0]] = {}
            pre_strain = row[0]
            total_nums[row[0]] = 0
            unknown_nums[row[0]] = 0
        if row[5] not in subs[row[0]].keys():
            subs[row[0]][row[5]] = 1
        else:
            if row[5] == "Unknown":
                unknown_nums[row[0]] += 1
            subs[row[0]][row[5]] += 1
            total_nums[row[0]] += 1
        if row[5] not in subs["all_strain"].keys():
            subs["all_strain"][row[5]] = 1
        else:
            if row[5] == "Unknown":
                unknown_nums["all_strain"] += 1
            subs["all_strain"][row[5]] += 1
            total_nums["all_strain"] += 1

def print_file_and_plot(sub, total_nums, unknown_nums, strain, out_stat, prefix_name):
    plot(sub, total_nums[strain], unknown_nums[strain], strain, prefix_name)
    out_stat.write(strain + ":\n")
    out_stat.write("Total with Unknown is {0}; Total_wihout_Unknown is {1}\n".format(
                   total_nums[strain], total_nums[strain] - unknown_nums[strain]))
    for local, num in sub.items():
        if local != "Unknown":
            out_stat.write("\t{0}\t{1}(include Unknown {2}; exclude Unknonwn {3})\n".format(
            local, num, float(num) / float(total_nums[strain]),
            float(num) / (float(total_nums[strain]) - float(unknown_nums[strain]))))
        else:
            out_stat.write("\t{0}\t{1}(include Unknown {2})\n".format(
            local, num, float(num) / float(total_nums[strain])))

def stat_sublocal(psortb_file, prefix_name, stat_file):
    subs = {}
    subs["all_strain"] = {}
    total_nums = {}
    total_nums["all_strain"] = 0
    unknown_nums = {}
    unknown_nums["all_strain"] = 0
    read_table(psortb_file, subs, total_nums, unknown_nums)
    out_stat = open(stat_file, "w")
    if len(subs) > 2:
        print_file_and_plot(sub["all_strain"], total_nums, unknown_nums, 
                            "all_strain", out_stat, prefix_name)
    for strain, sub in subs.items():
        if strain != "all_strain":
            print_file_and_plot(sub, total_nums, unknown_nums, strain, 
                                out_stat, prefix_name)
