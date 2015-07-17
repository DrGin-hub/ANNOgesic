#!/usr/bin/python

import os
import sys
import shutil
from subprocess import call, Popen
from annogesiclib.helper import Helper
from annogesiclib.multiparser import Multiparser
from annogesiclib.converter import Converter
from annogesiclib.get_inter_seq import intergenic_seq
from annogesiclib.get_polyT import poly_t
from annogesiclib.detect_coverage_term import detect_coverage
from annogesiclib.gff3 import Gff3Parser
from annogesiclib.stat_term import stat_term


class Terminator(object):

    def __init__(self, gffs, fastas, trans, out_folder, sRNAs):
        self.multiparser = Multiparser()
        self.helper = Helper()
        self.converter = Converter()
        self.gff_parser = Gff3Parser()
        self.gff_path = os.path.join(gffs, "tmp")
        self.fasta_path = os.path.join(fastas, "tmp")
        self.tran_path = os.path.join(trans, "tmp")
        self.outfolder = {"term": os.path.join(out_folder, "gffs"),
                          "csv": os.path.join(out_folder, "tables")}
        self.terms = {"all": os.path.join(self.outfolder["term"],
                                          "all_candidates"),
                      "express": os.path.join(self.outfolder["term"],
                                              "express"),
                      "detect": os.path.join(self.outfolder["term"], "detect")}
        self.csvs = {"all": os.path.join(self.outfolder["csv"],
                                         "all_candidates"),
                     "express": os.path.join(self.outfolder["csv"], "express"),
                     "detect": os.path.join(self.outfolder["csv"], "detect")}
        self.combine_path = os.path.join(self.gff_path, "combine")
        self.tmps = {"transterm": os.path.join(os.getcwd(), "tmp_transterm"),
                     "hp": "transtermhp", "hp_gff": "transtermhp.gff",
                     "hp_path": "tmp_transterm/tmp", 
                     "term_table": os.path.join(os.getcwd(), "tmp_term_table"),
                     "merge": os.path.join(os.getcwd(), "tmp_merge_gff"),
                     "gff": "tmp.gff",
                     "folder": os.path.join(os.getcwd(), "tmp")}
        self.suffixs = {"gff": "term.gff", "csv": "term.csv",
                        "allgff": "term_all.gff"}
        if sRNAs:
            self.srna_path = os.path.join(sRNAs, "tmp")
        else:
            self.srna_path = None
        self._make_gff_folder()


    def _combine_annotation(self, combine_file, files):
        with open(combine_file, 'w') as result:
            for file_ in files:
                check_start = False
                for line in open( file_, 'r' ):
                    if check_start:
                        result.write(line)
                    if "Location" in line:
                        check_start = True

    def _make_gff_folder(self):
        self.helper.check_make_folder(self.terms["all"])
        self.helper.check_make_folder(self.csvs["all"])
        self.helper.check_make_folder(self.terms["detect"])
        self.helper.check_make_folder(self.csvs["detect"])
        self.helper.check_make_folder(self.terms["express"])
        self.helper.check_make_folder(self.csvs["express"])

    def _convert_gff2rntptt(self, gff_path, prefixs,
                            fasta_path, sRNAs, file_types):
        for gff in os.listdir(gff_path):
            if gff.endswith(".gff"):
                filename = gff.split("/")
                prefix = filename[-1][:-4]
                prefixs.append(prefix)
                gff_file = os.path.join(gff_path, gff)
                rnt_file = os.path.join(gff_path, gff.replace(".gff", ".rnt"))
                ptt_file = os.path.join(gff_path, gff.replace(".gff", ".ptt"))
                fasta = self.helper.get_correct_file(
                             fasta_path, ".fa", prefix, None)
                if not fasta:
                    print("Error: no proper file - {0}.fa".format(prefix))
                    sys.exit()
                if sRNAs:
                    self.multiparser.parser_gff(sRNAs, "sRNA")
                    srna = self.helper.get_correct_file(
                                self.srna_path, "_sRNA.gff", prefix, None)
                    if (srna) and (fasta):
                        self.converter.convert_gff2rntptt(gff_file, fasta,
                             ptt_file, rnt_file, srna,
                             srna.replace(".gff", ".rnt"))
                        file_types[prefix] = "srna"
                    if (not srna) and (fasta):
                        self.converter.convert_gff2rntptt(gff_file, fasta,
                             ptt_file, rnt_file, None, None)
                        file_types[prefix] = "normal"
                else:
                    self.converter.convert_gff2rntptt(gff_file, fasta,
                         ptt_file, rnt_file, None, None)
                    file_types[prefix] = "normal"

    def _combine_ptt_rnt(self, gff_path, file_types, srna_path):
        self.helper.check_make_folder(self.combine_path)
        for prefix, file_type in file_types.items():
            combine_file = os.path.join(self.combine_path, prefix + '.ptt')
            if file_type == "normal":
                files = [os.path.join(gff_path, prefix + ".ptt"),
                         os.path.join(gff_path, prefix + ".rnt")]
                self._combine_annotation(combine_file, files)
            elif file_type == "srna":
                files = [os.path.join(gff_path, prefix + ".ptt"),
                         os.path.join(gff_path, prefix + ".rnt"),
                         os.path.join(srna_path,
                                      "_".join([prefix, "sRNA.rnt"]))]
                self._combine_annotation(combine_file, files)

    def _run_TransTermHP(self, TransTermHP_path, combine_path,
                         fasta_path, hp_folder, expterm_path):
        self.helper.check_make_folder(self.tmps["transterm"])
        for file_ in os.listdir(combine_path):
            if ".ptt" in file_:
                prefix = file_.replace(".ptt", "")
                fasta = self.helper.get_correct_file(
                             fasta_path, ".fa", prefix, None)
                if not fasta:
                    print("Error: no proper file - {0}.fa".format(prefix))
                    sys.exit()
                out_path = os.path.join(hp_folder, prefix)
                self.helper.check_make_folder(out_path)
                out = open(os.path.join(out_path,
                           "_".join([prefix, "terminators.txt"])), "w")
                call([TransTermHP_path, "-p", expterm_path,
                      fasta, os.path.join(combine_path, file_), "--t2t-perf",
                      os.path.join(out_path,
                      "_".join([prefix,
                      "terminators_within_robust_tail-to-tail_regions.t2t"])),
                      "--bag-output", os.path.join(out_path,
                      "_".join([prefix, "best_terminator_after_gene.bag"]))],
                      stdout=out)
        shutil.rmtree(combine_path)

    def _convert_to_gff(self, prefixs, hp_folder, gffs):
        for prefix in prefixs:
            for folder in os.listdir(hp_folder):
                if prefix == folder:
                    out_path = os.path.join(hp_folder, folder)
                    for file_ in os.listdir(out_path):
                        if file_.endswith(".bag"):
                            out_file = os.path.join(self.tmps["transterm"],
                                       "_".join([prefix, self.tmps["hp_gff"]]))
                            self.converter.convert_transtermhp2gff(
                                 os.path.join(out_path, file_), out_file)
        self.multiparser.combine_gff(gffs, self.tmps["transterm"],
                                      None, self.tmps["hp"])

    def _combine_libs_wigs(self, tlibs, flibs, tex_wigs, frag_wigs):
        if (tlibs is None) and (flibs is None):
            print("Error: please input proper libraries!!")
        if (tlibs is not None) and (flibs is not None):
            libs = tlibs + flibs
        elif (tlibs is not None):
            libs = tlibs
        elif (flibs is not None):
            libs = flibs
        if (tex_wigs is not None) and (frag_wigs is not None):
            folder = tex_wigs.split("/")
            folder = "/".join(folder[:-1])
            merge_wigs = os.path.join(folder, "merge_wigs")
            self.helper.check_make_folder(merge_wigs)
            for wig in os.listdir(tex_wigs):
                if os.path.isdir(os.path.join(tex_wigs, wig)):
                    pass
                else:
                    shutil.copy(os.path.join(tex_wigs, wig), merge_wigs)
            for wig in os.listdir(frag_wigs):
                if os.path.isdir(os.path.join(frag_wigs, wig)):
                    pass
                else:
                    shutil.copy(os.path.join(frag_wigs, wig), merge_wigs)
        elif (tex_wigs is not None):
            merge_wigs = tex_wigs
        elif (frag_wigs is not None):
            merge_wigs = frag_wigs
        else:
            print("Error: no proper wig files!!!")
            sys.exit()
        return (merge_wigs, libs)

    def _merge_sRNA(self, sRNAs, prefixs, gff_path, srna_path):
        if sRNAs is not None:
            self.multiparser.parser_gff(sRNAs, "sRNA")
            srna_path = os.path.join(sRNAs, "tmp")
            self.helper.check_make_folder(self.tmps["merge"])
            for prefix in prefixs:
                tmp_gff = os.path.join(self.tmps["merge"], self.tmps["gff"])
                if self.tmps["gff"] in os.listdir(self.tmps["merge"]):
                    os.remove(tmp_gff)
                self.helper.merge_file(os.path.join(gff_path, prefix + ".gff"),
                            tmp_gff)
                self.helper.merge_file(os.path.join(srna_path,
                            "_".join([prefix, "sRNA.gff"])), tmp_gff)
                self.helper.sort_gff(tmp_gff, os.path.join(self.tmps["merge"],
                            prefix + ".gff"))
                os.remove(tmp_gff)
            merge_path = self.tmps["merge"]
        else:
            merge_path = gff_path
        return merge_path

    def _move_file(self, term_outfolder, csv_outfolder):
        for gff in os.listdir(term_outfolder):
            if gff.endswith("_term.gff"):
                self.helper.sort_gff(os.path.join(term_outfolder, gff),
                                     self.tmps["gff"])
                os.rename(self.tmps["gff"], os.path.join(term_outfolder, gff))
                prefix = gff.replace("_term.gff", "")
                new_gff = os.path.join(self.terms["all"],
                          "_".join([prefix, self.suffixs["allgff"]]))
                csv_file = os.path.join(os.path.join(self.csvs["all"],
                           "_".join([prefix, self.suffixs["csv"]])))
                out = open(new_gff, "w")
                out.write("##gff-version 3\n")
                out.close()
                self.helper.merge_file(os.path.join(term_outfolder, gff),
                            os.path.join(self.terms["all"],
                            "_".join([prefix, self.suffixs["allgff"]])))
                os.remove(os.path.join(term_outfolder, gff))
                pre_strain = ""
                if "_".join([prefix, self.suffixs["csv"]]) in \
                             os.listdir(self.csvs["all"]):
                    os.remove(csv_file)
                out_csv = open(csv_file, "w")
                out_csv.write("\t".join(["strain", "name", "start", "end",
                              "strand", "detect", "coverage_detail"]) + "\n")
                out_csv.close()
                for entry in self.gff_parser.entries(open(new_gff)):
                    if entry.seq_id != pre_strain:
                        self.helper.merge_file(
                             os.path.join(self.tmps["term_table"],
                             "_".join([entry.seq_id, "term_raw.csv"])),
                             os.path.join(self.csvs["all"],
                             "_".join([prefix, self.suffixs["csv"]])))
                    pre_strain = entry.seq_id

    def _compute_intersection_forward_reverse(self, RNAfold_path, prefixs,
                tran_path, merge_path, fasta_path, cutoff_coverage, fuzzy,
                wig_path, merge_wigs, libs, tex_notex, replicates, decrease,
                term_outfolder, csv_outfolder, table_best, gffs, out_folder,
                fuzzy_up_ta, fuzzy_down_ta, fuzzy_up_cds, fuzzy_down_cds):
        for prefix in prefixs:
            tmp_seq = os.path.join(out_folder,
                      "_".join(["inter_seq", prefix]))
            tmp_sec = os.path.join(out_folder,
                      "_".join(["inter_sec", prefix]))
            tran_file = os.path.join(tran_path,
                        "_".join([prefix, "transcript.gff"]))
            gff_file = os.path.join(merge_path, prefix + ".gff")
            ### get intergenic seq, sec
            print("Extracting seq of {0}".format(prefix))
            out_seq = open(tmp_seq, "w")
            intergenic_seq(os.path.join(fasta_path, prefix + ".fa"),
                           tran_file, gff_file, tmp_seq)
            print("Computing secondray structure of {0}".format(prefix))
            self.helper.check_make_folder(self.tmps["folder"])
            pre_cwd = os.getcwd()
            os.chdir(self.tmps["folder"])
            os.system(" ".join([RNAfold_path, "<", os.path.join("..", tmp_seq),
                                ">", os.path.join("..", tmp_sec)]))
            os.chdir(pre_cwd)
            shutil.rmtree(self.tmps["folder"])
            ### detect poly U/T tail of terminators and coverage decreasing.
            tmp_cand = os.path.join(out_folder,
                       "_".join(["term_candidates", prefix]))
            poly_t(tmp_seq, tmp_sec, gff_file, tran_file, fuzzy_up_ta,
                   fuzzy_down_ta, fuzzy_up_cds, fuzzy_down_cds, tmp_cand)
            print("detection of terminator")
            detect_coverage(tmp_cand, os.path.join(merge_path, prefix + ".gff"),
                os.path.join(tran_path, "_".join([prefix, "transcript.gff"])),
                os.path.join(fasta_path, prefix + ".fa"),
                os.path.join(wig_path, "_".join([prefix, "forward.wig"])),
                os.path.join(wig_path, "_".join([prefix, "reverse.wig"])),
                fuzzy, cutoff_coverage, os.path.join(self.tmps["hp_path"],
                "_".join([prefix, self.tmps["hp_gff"]])), merge_wigs, libs,
                tex_notex, replicates, os.path.join(term_outfolder,
                "_".join([prefix, self.suffixs["gff"]])),
                os.path.join(self.tmps["term_table"],
                "_".join([prefix, "term_raw.csv"])), table_best, decrease)
        self.multiparser.combine_gff(gffs, term_outfolder, None, "term")
        self._move_file(term_outfolder, csv_outfolder)
        
    def _remove_tmp_file(self, gffs, fastas, sRNAs, tex_wigs, frag_wigs,
                         term_outfolder, out_folder, merge_wigs):
        self.helper.remove_tmp(gffs)
        self.helper.remove_tmp(fastas)
        if sRNAs is not None:
            self.helper.remove_tmp(sRNAs)
            shutil.rmtree(self.tmps["merge"])
        if (tex_wigs is not None) and (frag_wigs is not None):
            shutil.rmtree(merge_wigs)
        self.helper.remove_tmp(tex_wigs)
        self.helper.remove_tmp(frag_wigs)
        self.helper.remove_tmp(term_outfolder)
        shutil.rmtree(self.tmps["transterm"])
        shutil.rmtree(self.tmps["term_table"])
        self.helper.remove_all_content(out_folder, "inter_seq_", "file")
        self.helper.remove_all_content(out_folder, "inter_sec_", "file")
        self.helper.remove_all_content(out_folder, "term_candidates_", "file")

    def _compute_stat(self, term_outfolder, csv_outfolder, stat, out_folder):
        new_prefixs = []
        for gff in os.listdir(self.terms["all"]):
            if gff.endswith("_term_all.gff"):
                out_tmp = open(self.tmps["gff"], "w")
                out_tmp.write("##gff-version 3\n")
                new_prefix = gff.replace("_term_all.gff", "")
                new_prefixs.append(gff.replace("_term_all.gff", ""))
                num = 0
                for entry in self.gff_parser.entries(
                             open(os.path.join(self.terms["all"], gff))):
                    name = '%0*d' % (5, num)
                    entry.attributes["ID"] = "term" + str(num)
                    entry.attributes["Name"] = "_".join(["Terminator_" + name])
                    entry.attribute_string = ";".join(
                        ["=".join(items) for items in entry.attributes.items()])
                    out_tmp.write("\t".join([entry.info_without_attributes,
                                  entry.attribute_string]) + "\n")
                    num += 1
                out_tmp.close()
                os.rename(self.tmps["gff"], os.path.join(self.terms["all"],
                          "_".join([new_prefix, self.suffixs["gff"]])))
        if stat:
            stat_path = os.path.join(out_folder, "statistics")
            for prefix in new_prefixs:
                stat_term(os.path.join(self.terms["all"],
                          "_".join([prefix, self.suffixs["gff"]])),
                          os.path.join(self.csvs["all"],
                          "_".join([prefix, self.suffixs["csv"]])),
                          os.path.join(stat_path,
                          "_".join(["stat", prefix + ".csv"])),
                          os.path.join(self.terms["detect"],
                          "_".join([prefix, "term"])),
                          os.path.join(self.terms["express"],
                          "_".join([prefix, "term"])))
                os.rename(os.path.join(self.terms["detect"],
                          "_".join([prefix, self.suffixs["csv"]])),
                          os.path.join(self.csvs["detect"],
                          "_".join([prefix, self.suffixs["csv"]])))
                os.rename(os.path.join(self.terms["express"],
                          "_".join([prefix, self.suffixs["csv"]])),
                          os.path.join(self.csvs["express"],
                          "_".join([prefix, self.suffixs["csv"]])))
                os.remove(os.path.join(self.terms["all"],
                          "_".join([prefix, self.suffixs["allgff"]])))

    def _check_gff_file(self, folder):
        for file_ in os.listdir(folder):
            if file_.endswith(".gff"):
                self.helper.check_uni_attributes(os.path.join(folder, file_))

    def run_terminator(self, TransTermHP_path, expterm_path, RNAfold_path,
                       out_folder, fastas, gffs, trans, sRNAs, stat, tex_wigs,
                       frag_wigs, decrease, cutoff_coverage, fuzzy, fuzzy_up_ta,
                       fuzzy_down_ta, fuzzy_up_cds, fuzzy_down_cds, hp_folder,
                       tlibs, flibs, tex_notex, replicates_tex, replicates_frag,
                       table_best):
        if (replicates_tex is not None) and (replicates_frag is not None):
            replicates = {"tex": int(replicates_tex),
                          "frag": int(replicates_frag)}
        elif replicates_tex is not None:
            replicates = {"tex": int(replicates_tex), "frag": -1}
        elif replicates_frag is not None:
            replicates = {"tex": -1, "frag": int(replicates_frag)}
        else:
            print("Error:No replicates number assign!!!")
            sys.exit()
        ### First, running TransTermHP. Before, running TransTermHP,
        ### we need to convert annotation files to .ptt and .rnt files.
        file_types = {}
        prefixs = []
        self._check_gff_file(gffs)
        self._check_gff_file(trans)
        self.multiparser.parser_gff(gffs, None)
        self.multiparser.parser_fasta(fastas)
        if (not gffs) or (not fastas):
            print("Error: please assign gff annotation folder and fasta folder!!!")
            sys.exit()
        self._convert_gff2rntptt(self.gff_path, prefixs,
                                 self.fasta_path, sRNAs, file_types)
        self._combine_ptt_rnt(self.gff_path, file_types, self.srna_path)
        self._run_TransTermHP(TransTermHP_path, self.combine_path,
                              self.fasta_path, hp_folder, expterm_path)
        self._convert_to_gff(prefixs, hp_folder, gffs)
        lib_datas = self._combine_libs_wigs(tlibs, flibs, tex_wigs, frag_wigs)
        merge_wigs = lib_datas[0]
        libs = lib_datas[1]
        self.multiparser.parser_gff(self.gff_path, None)
        wig_path = os.path.join(merge_wigs, "tmp")
        self.multiparser.parser_wig(merge_wigs)
        self.multiparser.combine_wig(self.gff_path, wig_path, None)
        self.helper.remove_tmp(self.gff_path)
        self.multiparser.parser_gff(trans, "transcript")
        self.helper.check_make_folder(self.tmps["term_table"])
        self.multiparser.parser_gff(self.tmps["transterm"], self.tmps["hp"])
        merge_path = self._merge_sRNA(sRNAs, prefixs, self.gff_path,
                                      self.srna_path)
        ### Second, running the cross regions of forward and reverese strand.
        self._compute_intersection_forward_reverse(RNAfold_path, prefixs,
            self.tran_path, merge_path, self.fasta_path, cutoff_coverage, fuzzy,
            wig_path, merge_wigs, libs, tex_notex, replicates, decrease,
            self.outfolder["term"], self.outfolder["csv"], table_best, gffs,
            out_folder, fuzzy_up_ta, fuzzy_down_ta, fuzzy_up_cds, fuzzy_down_cds)
        self._compute_stat(self.outfolder["term"], self.outfolder["csv"],
                           stat, out_folder)
        self._remove_tmp_file(gffs, fastas, sRNAs, tex_wigs, frag_wigs,
                              self.outfolder["term"], out_folder, merge_wigs)