#!/usr/bin/env python
# -*- coding: utf-8 -*-
## auto last change for vim and Emacs: (whatever comes last)
## Latest change: Mon Mar 08 11:49:34 CET 2010
## Time-stamp: <2012-07-07 13:57:00 vk>
"""
analyze_artifacts_tagstore.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by Karl Voit <Karl.Voit@IST.TUGraz.at>
:license: GPL v2 or any later version
:bugreports: <Karl.Voit@IST.TUGraz.at>

See USAGE below for details!

FIXXME:
    * look for the string FIXXME to improve this script
    * encoding problems with tags containing German umlauts

"""

import logging    # logging
import sys        # flushing stdout
import os         # accessing file system
from optparse import OptionParser  # parsing command line options
import re         # RegEx
import codecs     # fixing UTF-8 issues
from numpy import *  # computing standard deviation
from glob import glob  # file globbing is not done by the shell on Windows

## for CSV
import csv

## debugging:   for setting a breakpoint:  pdb.set_trace()
import pdb

#counts the distinct words
from collections import defaultdict

#filenames
file_sum_tags = "sum_tags.csv"
file_sum_items = "sum_items.csv"
file_tags_per_item = "tag_per_item.csv"
file_tag_length = "tag_length.csv"

## ======================================================================= ##
##                                                                         ##
##         You should NOT need to modify anything below this line!         ##
##                                                                         ##
## ======================================================================= ##

## example:   Winterurlaub%20ist%20Schiurlaub.pdf\tags="news,urlaub"
FILEENTRY_REGEX = re.compile("(.+)\\\\tags=(\")?(.+(,)?)+(\")?$")
## group 1 = itemname
## group 3 = string of tags, concatenated with ","


USAGE = "\n\
         %prog tagstore*.tgs\n\
\n\
This script reads in one or multiple store.tgs files of tagstore\n\
(probably renamed to something like \"TP42_store.tgs\") and calculates\n\
misc statistical data.\n\
Output will be written to CSV files.\n\
\n\
  :URL:        https://github.com/novoid/2011-04-tagstore-formal-experiment\n\
  :copyright:  (c) 2012 by Karl Voit <Karl.Voit@IST.TUGraz.at>\n\
  :license:    GPL v2 or any later version\n\
  :bugreports: <Karl.Voit@IST.TUGraz.at>\n\
\n\
Run %prog --help for usage hints\n"

parser = OptionParser(usage=USAGE)

parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                  help="enable verbose mode")

parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                  help="do not output anything but just errors on console")

(options, args) = parser.parse_args()


class vk_FileNotFoundException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class testperson:
    def __init__(self, number, tag_count, item_count,
                 word_list, single_item_tag_count):
        self.number = number
        self.tag_count = tag_count
        self.item_count = item_count
        self.word_list = word_list
        self.single_item_tag_count = array(single_item_tag_count)

        # calculations
        self.tags_per_item = float(self.tag_count) / float(self.item_count)
        self.tags_per_item_stddev = self.single_item_tag_count.std()

    def __repr__(self):
        return """TP number: %s, tag_count: %s, item_count: %s\n\
                  word_list: %s\n""" % (
            self.number, self.tag_count, self.item_count, self.word_list)


def handle_logging():
    """Log handling and configuration"""

    if options.verbose:
        FORMAT = "%(levelname)-8s %(asctime)-15s %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    elif options.quiet:
        FORMAT = "%(levelname)-8s %(message)s"
        logging.basicConfig(level=logging.CRITICAL, format=FORMAT)
    else:
        FORMAT = "%(message)s"
        logging.basicConfig(level=logging.INFO, format=FORMAT)


def error_exit(errorcode, text):
    """exits with return value of errorcode and prints to stderr"""

    sys.stdout.flush()
    logging.error(text + "\n")
    sys.exit(errorcode)


def guess_tp_number(string):
    """parses a string for occurrence of a number"""

    ## replacing all non-digits from the string and converting it to a integer
    digits = re.sub("\D", "", string)

    if not digits:
        error_exit(3, "ERROR: filename \"" + string +
                   "\" contains no digit which " +
                   "could lead to a TP number.\n" +
                   "Please keep TP numbers in file names.")

    return int(digits)


def desanitize(string):
    """reverse sanitizing of strings"""

    ## FIXXME: maybe more characters are sanitized?
    return string.replace('%20', ' ')


def handle_filename(filename):
    """Processes one tagstore.tgs file and store item/tag information"""

    logging.debug("\n")
    logging.info("====> processing file [%s]" % filename)

    if not os.path.isfile(filename):
        error_exit(2, "ERROR: \"%s\" is not a file." % filename)

    tpnumber = guess_tp_number(filename)
    logging.info("I guess this is TP number %s" % str(tpnumber))

    tpdata = {'TPnum': tpnumber, 'items': []}  # initialize
                                               # data structure for TP

    for line in codecs.open(filename, 'r', "utf-8"):
        components = FILEENTRY_REGEX.match(line.strip())
        if components:

            itemname = desanitize(components.group(1))  # fix sanitizing of
                                                        # space character

            logging.debug("---- match:    [%s]" % line.strip())
            logging.debug("  itemname: [%s]" % itemname)

            itemdata = {'name': itemname, 'tags': []}  # initialize data
                                                       # structure for item

            taglist = components.group(3).split(',')

            ## hack: correct doublequote character of last tag:
            if taglist[-1][-1:] == '"':
                taglist[-1] = taglist[-1][:-1]

            for tag in taglist:
                #logging.debug("  tag: [%s]" % tag)
                itemdata['tags'].append(desanitize(tag))

            tpdata['items'].append(itemdata)
            #logging.debug("finished parsing one item")
    #pdb.set_trace()
    logging.debug("Finished parsing TP file \"%s\"" % filename)

    #pdb.set_trace()
    return tpdata


def traverse_dataset(dataset, tp_list):
    """traverses the data structure of tpdata"""
    for tp in dataset:
        # init
        tag_count = 0
        item_count = 0
        word_list = []
        single_item_tag_count = []
        tag_length = []

        # calc
        for item in tp['items']:
            single_item_counter = 0
            item_count = item_count + 1
            for tag in item['tags']:
                single_item_counter = single_item_counter + 1
                tag_count = tag_count + 1
                word_list.append(tag)
            single_item_tag_count.append(single_item_counter)

        # finalize
        tp_list.append(testperson(tp['TPnum'], tag_count, item_count,
                       word_list, single_item_tag_count))
    #logging.debug("tp_list = %s" % tp_list)

    #calc_sum_tags(dataset)
    # logging.debug("=========== dataset DUMP =================")
    # logging.debug("dataset has %s TPs" % str(len(dataset)))
    # for tp in dataset:
    #     logging.debug("TP number %s has %s items" % (str(tp['TPnum']),
    #                   str(len(tp['items']))))
    #     for item in tp['items']:
    #         logging.debug("  item \"%s\" has %s tags" % (item['name'],
    #                       str(len(item['tags']))))
    #         for tag in item['tags']:
    #             logging.debug("    tag \"%s\" has length %s" % (tag,
    #    len(tag)))


def calc_tags_per_item(tp_list):
    tp_list = sorted(tp_list, key=lambda testperson: testperson.tags_per_item)
    with open(file_tags_per_item, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["TP Number", "Avg. Tags/Item", "Standard Deviation"])
        for tp in tp_list:
            logging.debug(tp.tags_per_item)
            writer.writerow([tp.number, tp.tags_per_item,
                             tp.tags_per_item_stddev])
    logging.info("File written: %s" % file_tags_per_item)


def calc_sum_tags(tp_list):
    tp_list = sorted(tp_list, key=lambda testperson: testperson.number)
    with open(file_sum_tags, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["TP Number", "Tag Count"])  # write header
        for tp in tp_list:
            writer.writerow([tp.number, tp.tag_count])
    logging.info("File written: %s" % file_sum_tags)


def calc_sum_items(tp_list):
    tp_list = sorted(tp_list, key=lambda testperson: testperson.number)
    with open(file_sum_items, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["TP Number", "Item Count"])  # write header
        for tp in tp_list:
            writer.writerow([tp.number, tp.item_count])
    logging.info("File written: %s" % file_sum_items)


def calc_tag_length(tp_list):
    tp_list = sorted(tp_list, key=lambda testperson: testperson.number)
    with open(file_tag_length, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["TP Number", "Avg. Tag Length", "Standard Deviation"])
        for tp in tp_list:
            writer.writerow([tp.number, tp.tag_length, tp.tag_length_stddev])
    logging.info("File written: %s" % file_tag_length)


def write_csv(tp_list):
    calc_tags_per_item(tp_list)  # five points!
    calc_sum_tags(tp_list)  # done
    calc_sum_items(tp_list)  # done
#     calc_tag_length()
#     calc_tag_variety_unique()
#     calc_tag_variety_sum()
#     calc_tag_single_usage()
#     calc_usage_normalized()


def main():
    """Main function [make pylint happy :)]"""

    print "                analyze_artifacts_tagstore.py\n"
    print "          (c) 2012 by Karl Voit <Karl.Voit@IST.TUGraz.at>"
    print "              GPL v2 or any later version\n"

    handle_logging()

    if len(args) < 1:
        parser.error("Please add at least one file name as argument")

    dataset = []  # initialize the dataset

    for argument in args:
        logging.debug("Received input %s" % (argument))
        arg_list = []
        arg_list = (glob(argument))
        for filename in arg_list:
            dataset.append(handle_filename(filename))
#    for filename in glob(args[0]):
#        dataset.append(handle_filename(filename))

    logging.debug("Parsed all files")

    tp_list = []  # initialize the list of test persons

    traverse_dataset(dataset, tp_list)

    write_csv(tp_list)

    logging.info("Finished")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Received KeyboardInterrupt")

## END OF FILE
#################################################################
# vim:foldmethod=indent expandtab ai ft=python
# vim:tw=120 fileencoding=utf-8 shiftwidth=4
