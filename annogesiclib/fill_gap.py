#!/usr/bin/python

import os
import sys
import csv
from annogesiclib.gff3 import Gff3Parser

def uni(tas, genes, out):
    start_tmp=0
    stop_tmp=0
    check=0
    for ta in tas:
        for gene in genes:
            if (ta.strand == gene.strand) and \
               (ta.seq_id == gene.seq_id):
                if ((ta.start < gene.start) and (ta.end > gene.start) and (ta.end < gene.end)) or \
                   ((ta.start > gene.start) and (ta.end < gene.end)) or \
                   ((ta.start > gene.start) and (ta.start < gene.end) and (ta.end > gene.end)):
                    check = 1
        if (check == 0) and (start_tmp != ta.start) and (stop_tmp != ta.end):
            out.write(ta.info + "\n")
            start_tmp = ta.start
            stop_tmp = ta.end
        check = 0

def overlap(tas, genes, print_list, out):
    start_tmp=0
    stop_tmp=0
    printed = 0
    check=0
    combine = False
    for gene in genes:
        start_tmp = 0
        stop_tmp = 0
        for ta in tas:
            if (ta.strand == gene.strand) and \
               (ta.seq_id == gene.seq_id):
                if ((ta.start < gene.start) and (ta.end > gene.start) and (ta.end < gene.end)) or \
                   ((ta.start > gene.start) and (ta.end < gene.end)) or \
                   ((ta.start > gene.start) and (ta.start < gene.end) and (ta.end > gene.end)):
                    check = 1
                    if ta in print_list:
                        printed = 1
                    else:
                        print_list.append(ta)
                    tmp_ta = ta
                    if start_tmp == 0:
                        start_tmp = ta.start
                        stop_tmp = ta.end
                    else:
                        combine = True
                        if stop_tmp < ta.end:
                            stop_tmp = ta.end
                if (ta.start > gene.end) and (start_tmp != 0):
                    check = 0
                    if combine or (printed != 1):
                        out.write("\t".join([str(field) for field in [ \
                                  ta.seq_id, ta.source, ta.feature, start_tmp, stop_tmp, \
                                  ta.score, ta.strand, ta.phase, ta.attribute_string]]) + "\n")
                    combine = False
                    printed = 0
                    break
        if (start_tmp != 0) and (check != 0):
            if combine or (printed != True):
                out.write('\t'.join([str(field) for field in [ \
                          ta.seq_id, ta.source, ta.feature, start_tmp, stop_tmp, \
                          ta.score, ta.strand, ta.phase, ta.attribute_string]]) + "\n")
def fill_gap(gff_file, ta_file, type_, output):
    tas = []
    genes = []
    print_list = []
    ta_f = open(ta_file, "r");
    gff_f = open(gff_file, "r");
    for entry in Gff3Parser().entries(ta_f):
        tas.append(entry)
    ta_f.close()
    for entry in Gff3Parser().entries(gff_f):
        if entry.feature == "gene":
            genes.append(entry)
    gff_f.close()
    out = open(output, "w")
    out.write("##gff-version 3\n")
    if type_ == "overlap":
        overlap(tas, genes, print_list, out)
    elif type_ == "uni":
        uni(tas, genes, out)

def print_file(ta, num, out):
    ta.attributes["ID"] = "tran" + str(num)
    ta.attributes["Name"] = "Transcript_" + ('%0*d' % (5, num))
    attribute_string = ";".join(
        ["=".join(items) for items in ta.attributes.items()])
    out.write("\t".join([str(field) for field in [
              ta.seq_id, ta.source, ta.feature, ta.start,
              ta.end, ta.score, ta.strand, ta.phase,
              attribute_string]]) + "\n")

def longer_ta(TA_file, length, out_file):
    tas = []
    confirms = []
    check = False
    for entry in Gff3Parser().entries(open(TA_file)):
        tas.append(entry)
    tas = sorted(tas, key=lambda k: (k.seq_id, k.start))
    for ta_1 in tas:
        for ta_2 in tas:
            if (ta_1.seq_id == ta_2.seq_id) and \
               (ta_1.strand == ta_2.strand):
                if (ta_1.start <= ta_2.start) and \
                   (ta_1.end >= ta_2.start) and \
                   (ta_1.end <= ta_2.end):
                    ta_1.end = ta_2.end
                elif (ta_1.start >= ta_2.start) and \
                     (ta_1.start <= ta_2.end) and \
                     (ta_1.end >= ta_2.end):
                    ta_1.start = ta_2.start
                elif (ta_1.start <= ta_2.start) and \
                     (ta_1.end >= ta_2.end):
                    pass
                elif (ta_1.start >= ta_2.start) and \
                     (ta_1.end <= ta_2.end):
                    ta_1.start = ta_2.start
                    ta_1.end = ta_2.end
    first = True
    out = open(out_file, "w")
    out.write("##gff-version 3\n")
    num = 0
    tas = sorted(tas, key=lambda k: (k.seq_id, k.start))
    for ta in tas:
        if (ta.end - ta.start) >= length:
            if first:
                first = False
                print_file(ta, num, out)
                num += 1
            else:
                if (ta.seq_id == pre_ta.seq_id) and \
                   (ta.strand == pre_ta.strand) and \
                   (ta.start == pre_ta.start) and \
                   (ta.end == pre_ta.end):
                    pass
                else:
                    print_file(ta, num, out)
                    num += 1
        pre_ta = ta
