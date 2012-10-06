#!/usr/bin/env python
# -*- coding: utf-8 -*-
## auto last change for vim and Emacs: (whatever comes last)
## Latest change: Mon Mar 08 11:49:34 CET 2010
## Time-stamp: <2012-07-07 13:57:00 vk>
"""
analyze_artifacts_tagstore.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by Karl Voit <Karl.Voit@IST.TUGraz.at>,
:                       Alexander Skiba <mail@ghostlyrics.net>
:license: GPL v2 or any later version
:bugreports: https://github.com/GhostLyrics/tagstore-logparser

See USAGE below for details!

FIXXME:
    * look for the string FIXXME to improve this script

"""

import logging    # logging
import sys        # flushing stdout
import os         # accessing file system
from optparse import OptionParser  # parsing command line options
import re         # RegEx
import codecs     # fixing UTF-8 issues

## maths
from numpy import array, std, sum, median, min, max, mean
from scipy.stats import scoreatpercentile
from pylab import boxplot, savefig, figure

## globbing on Windows
from glob import glob


## for CSV
import csv

## debugging:   for setting a breakpoint:  pdb.set_trace()
import pdb

#counts the distinct words
from collections import defaultdict

#filenames
file_extension = ".csv"

file_sum_tags = "sum_tags"
file_sum_items = "sum_items"
file_tags_per_item = "tag_per_item"
file_tag_length = "tag_length"
file_single_usage = "single_usage"
file_usage_normalized = "usage_normalized"

file_template_tag_variety = "tag_variety"
file_template_tag_reuse = "tag_reuse"

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
                           Alexander Skiba <mail@ghostlyrics.net>\n\
  :license:    GPL v2 or any later version\n\
  :bugreports: https://github.com/GhostLyrics/tagstore-logparser\n\
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
                 tag_list, number_tags_on_item_list):
        self.number = number
        self.tag_count = tag_count
        self.item_count = item_count
        self.tag_list = []
        self.number_tags_on_item_list = array(number_tags_on_item_list)

        # calculations: tags per item; has to be done this way in order to
        #               enable sorting of the list of testperson-objects
        self.tags_per_item = float(self.tag_count) / float(self.item_count)
        self.tags_per_item_stddev = self.number_tags_on_item_list.std()

        # encoding all tags to unicode
        for tag in tag_list:
            self.tag_list.append(tag.encode('utf-8'))

    def getAverageTagLength(self):
        # init
        tag_length_sum = 0

        # calc
        for tag in self.tag_list:
            tag_length_sum = tag_length_sum + len(tag)
        tag_length = float(tag_length_sum) / float(self.tag_count)
        return tag_length

    def buildTagLengthList(self):
        # init
        tag_length_list = []

        # calc
        for tag in self.tag_list:
            tag_length_list.append(len(tag))
        self.tag_length_list = array(tag_length_list)

    def buildTagDictionary(self):
        # init
        if not hasattr(self, 'unique_tag_dict'):
            unique_tag_dict = {}

            # calc
            for tag in self.tag_list:
                if tag in unique_tag_dict:  # if it's there, just increase
                    unique_tag_dict.update({tag: unique_tag_dict.get(tag) + 1})
                else:
                    unique_tag_dict.update({tag: 1})  # not there -> add it
            self.unique_tag_dict = unique_tag_dict
            logging.debug("Tag Dictionary for TP %s built" % self.number)

        else:
            logging.debug("Tag Dictionary for TP %s " % self.number
                          + "already exists, skipping build")

    def buildReuseDictionary(self):
        # init
        if not hasattr(self, 'reuse_dict'):
            reuse_dict = {}

            # calc
            for count in self.number_tags_on_item_list:
                if count in reuse_dict:
                    reuse_dict.update({count: reuse_dict.get(count) + 1})
                else:
                    reuse_dict.update({count: 1})
            self.reuse_dict = reuse_dict
            logging.debug("Usage Dictionary for TP %s built" % self.number)

        else:
            logging.debug("Usage Dictionary for TP %s " % self.number
                          + "already exists, skipping build")

    def getPercentageOfSingleTags(self):
        # init
        single_usage_tag_counter = 0
        percentage = 0
        self.buildTagDictionary()

        # run
        for tag in self.unique_tag_dict:
            if self.unique_tag_dict.get(tag) is 1:
                single_usage_tag_counter += 1
        percentage = (float(len(self.unique_tag_dict))  # not sure
                      / 100 * single_usage_tag_counter)  # I hope this is right
        return percentage

    def getUsageNormalized(self):
        # init
        mean_value = 0
        sum_usage = 0
        normalized_value = 0
        self.buildTagDictionary()

        # run
        for tag in self.unique_tag_dict:
            sum_usage = sum_usage + self.unique_tag_dict.get(tag)
        mean_value = sum_usage / float(len(self.unique_tag_dict))
        normalized_value = mean_value / self.item_count
        return normalized_value

    def __repr__(self):
        return "This is TP %s" % (self.number)


def fivenum(input_list):
    """Returns a dictionary with the five point summary for a given list"""
    q1 = scoreatpercentile(input_list, 25)
    q3 = scoreatpercentile(input_list, 75)
    md = median(input_list)

    five = {'min': min(input_list),
            'q1': q1,
            'med': md,
            'q3': q3,
            'max': max(input_list)}
    return five


def display(float_value):
    """Display nicer values and generally save typing"""
    return "{0:.2f}".format(float_value)


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
        tag_list = []
        number_tags_on_item_list = []
        tag_length = []

        # calc
        for item in tp['items']:
            single_item_counter = 0
            item_count += 1
            for tag in item['tags']:
                single_item_counter += 1
                tag_count += 1
                tag_list.append(tag)
            number_tags_on_item_list.append(single_item_counter)

        # finalize
        tp_list.append(testperson(tp['TPnum'], tag_count, item_count,
                       tag_list, number_tags_on_item_list))


def calc_tags_per_item(tp_list):
    # init
    filename = file_tags_per_item + file_extension
    filename_plot = file_tags_per_item + '_plot'
    tp_list = sorted(tp_list,
                     key=lambda testperson: testperson.tags_per_item,
                     reverse=True)

    # init global
    global_array = []  # contains all the values in order to generate a boxplot
                       # for all testpersons combined

    # run per testperson
    with open(filename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["TP Number",
                         "Avg. Tags/Item",
                         "Standard Deviation",
                         "Minimum",
                         "First Quartille",
                         "Median",
                         "Third Quartille",
                         "Maximum"])
        for tp in tp_list:
            # init
            global_array.append(tp.tags_per_item)
            fivenumbers = fivenum(tp.number_tags_on_item_list)

            # run
            writer.writerow([tp.number,
                            display(tp.tags_per_item),
                            display(tp.tags_per_item_stddev),
                            # in case you're wondering why this looks as ugly:
                            # there doesn't seem to be a way to use a list in
                            # here. So we have to use functions or variables
                            # every. single. time.
                            display(fivenumbers.get('min')),
                            display(fivenumbers.get('q1')),
                            display(fivenumbers.get('med')),
                            display(fivenumbers.get('q3')),
                            display(fivenumbers.get('max'))])
            figure()
            boxplot(tp.number_tags_on_item_list)  # TODO: axis description
            savefig(filename_plot + str(tp.number))
            logging.debug('Plot drawn: %s' % (filename_plot + str(tp.number)))
    logging.info("File written: %s" % (filename))

    # run global
    global_fivenumbers = fivenum(global_array)
    with open(('global_' + filename), 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(['Avg. Tags/Item',
                         'Standard Deviation',
                         'Minimum',
                         'First Quartille',
                         'Median',
                         'Third Quartille',
                         'Maximum'])
        writer.writerow([display(mean(global_array)),
                         display((std(global_array))),
                         display(global_fivenumbers.get('min')),
                         display(global_fivenumbers.get('q1')),
                         display(global_fivenumbers.get('med')),
                         display(global_fivenumbers.get('q3')),
                         display(global_fivenumbers.get('max'))])
    logging.info("File written: %s" % ('global_' + filename))
    figure()
    boxplot(global_array)  # TODO: axis description
    savefig('global_' + filename_plot)
    logging.debug("Plot drawn: %s" % ('global_' + filename_plot))


def calc_sum_tags(tp_list):
    # init
    filename = file_sum_tags + file_extension
    tp_list = sorted(tp_list, key=lambda testperson: testperson.number)

    # run
    with open(filename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["TP Number", "Tag Count"])
        for tp in tp_list:
            writer.writerow([tp.number, tp.tag_count])
    logging.info("File written: %s" % (filename))


def calc_sum_items(tp_list):
    # init
    filename = file_sum_items + file_extension
    tp_list = sorted(tp_list, key=lambda testperson: testperson.number)

    # run
    with open(filename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["TP Number", "Item Count"])
        for tp in tp_list:
            writer.writerow([tp.number, tp.item_count])
    logging.info("File written: %s" % (filename))


def calc_tag_length(tp_list):
    # init
    filename = file_tag_length + file_extension
    filename_plot = file_tag_length + '_plot'
    tp_list = sorted(tp_list, key=lambda testperson: testperson.number)

    # init global
    global_array = []  # contains all the values in order to generate a boxplot
                       # for all testpersons combined

    # run for test person
    with open(filename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["TP Number",
                         "Avg. Tag Length",
                         "Standard Deviation",
                         "Minimum",
                         "First Quartille",
                         "Median",
                         "Third Quartille",
                         "Maximum"])
        for tp in tp_list:
            # init
            tp.buildTagLengthList()
            for tag_length in tp.tag_length_list:
                global_array.append(tag_length)
            fivenumbers = fivenum(tp.tag_length_list)

            # run
            writer.writerow([tp.number,
                            display(tp.getAverageTagLength()),
                            display(tp.tag_length_list.std()),
                            display(fivenumbers.get('min')),
                            display(fivenumbers.get('q1')),
                            display(fivenumbers.get('med')),
                            display(fivenumbers.get('q3')),
                            display(fivenumbers.get('max'))])
            figure()
            boxplot(tp.tag_length_list)  # TODO: axis description
            savefig(filename_plot + str(tp.number))
            logging.debug('Plot drawn: %s' % (filename_plot + str(tp.number)))
    logging.info("File written: %s" % (filename))

    # run global
    global_fivenumbers = fivenum(global_array)
    with open(('global_' + filename), 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(['Avg. Tag Length',
                         'Standard Deviation',
                         'Minimum',
                         'First Quartille',
                         'Median',
                         'Third Quartille',
                         'Maximum'])
        writer.writerow([display(mean(global_array)),
                         display(std(global_array)),
                         display(global_fivenumbers.get('min')),
                         display(global_fivenumbers.get('q1')),
                         display(global_fivenumbers.get('med')),
                         display(global_fivenumbers.get('q3')),
                         display(global_fivenumbers.get('max'))])
    logging.info('File written: %s' % ('global_' + filename))
    figure()
    boxplot(global_array)  # TODO. axis description
    savefig('global_' + filename_plot)
    logging.debug('Plot drawn: %s' % ('global_' + filename_plot))


def calc_tag_variety(tp_list):
    for tp in tp_list:
        # init
        filename = file_template_tag_variety + str(tp.number) + file_extension
        tp.buildTagDictionary()  # build dict to sort for output
        tag_dict = sorted(tp.unique_tag_dict,
                          key=tp.unique_tag_dict.get,
                          reverse=True)

        # run
        with open(filename, "wb") as f:
            writer = csv.writer(f)
            writer.writerow(["Tag", "Usage Count"])
            for tag in tag_dict:
                writer.writerow([tag, tp.unique_tag_dict.get(tag)])
        logging.debug("File written: %s" % (filename))
    logging.info("Section written: %s" % (file_template_tag_variety))


def calc_tag_reuse(tp_list):
    for tp in tp_list:
        # init
        filename = file_template_tag_reuse + str(tp.number) + file_extension
        tp.buildReuseDictionary()
        reuse_dict = sorted(tp.reuse_dict, reverse=True)

        # run
        with open(filename, "wb") as f:
            writer = csv.writer(f)
            writer.writerow(["Tag Count per Item", "Occurrence"])
            for number in reuse_dict:
                writer.writerow([number, tp.reuse_dict.get(number)])
        logging.debug("File written: %s" % (filename))
    logging.info("Section written: %s" % (file_template_tag_reuse))


def calc_tag_single_usage(tp_list):
    # init
    filename = file_single_usage + file_extension
    tp_list = sorted(tp_list, key=lambda testperson: testperson.number)

    # run
    with open(filename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["TP Number",
                         "Percentage of Tags with single Occurrence"])
        for tp in tp_list:
            writer.writerow([tp.number,
                            display(tp.getPercentageOfSingleTags())])
    logging.info("File written: %s" % (filename))


def calc_usage_normalized(tp_list):
    # init
    filename = file_usage_normalized + file_extension
    tp_list = sorted(tp_list, key=lambda testperson: testperson.number)

    # run
    with open(filename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["TP Number",
                         "Average Usage of Tags, normalized"])
        for tp in tp_list:
            writer.writerow([tp.number,
                             display(tp.getUsageNormalized())])
    logging.info("File written: %s" % (filename))


def write_csv(tp_list):
    calc_tags_per_item(tp_list)  # done
    calc_sum_tags(tp_list)  # done
    calc_sum_items(tp_list)  # done
    calc_tag_length(tp_list)  # looks crappy
    calc_tag_variety(tp_list)  # done
    calc_tag_reuse(tp_list)  # done
    calc_tag_single_usage(tp_list)  # done
    calc_usage_normalized(tp_list)  # done


def main():
    """Main function [make pylint happy :)]"""

    print "                analyze_artifacts_tagstore.py\n"
    print "          (c) 2012 by Karl Voit <Karl.Voit@IST.TUGraz.at>,"
    print "                      Alexander Skiba <mail@ghostlyrics.net>"
    print "              GPL v2 or any later version\n"

    handle_logging()

    if len(args) < 1:
        parser.error("Please add at least one file name as argument")

    dataset = []  # initialize the dataset

    for argument in args:
        logging.debug("Received input %s\n" % (argument))
        arg_list = []
        arg_list = (glob(argument))
        for filename in arg_list:
            dataset.append(handle_filename(filename))

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
