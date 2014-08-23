#!/usr/bin/python 

"""
    A simple piece of python code that could convert the Brat annotation
tool format into Event Mention Detection format for easy evaluation. For
detailed features and usage please refer to the README file
"""
import argparse
import logging
import sys
import os
import errno

spanMarker = "T"
eventMarker = "E"
attMarker = "A"
attMarkerBack = "M" # for backward compatibility
noteMarker = "#"
bodMarker = "#BeginOfDocument" #mark begin of a document
eodMarker = "#EndOfDocument" #mark end of a document


textBounds = {} # all text bounds
events = {} # all events 
atts = {} # all attributes 

out = "converted"
outExt = "cbf" #short for character based format
engineId = "brat_conversion"
spanSeperator = ";"
spanJonier = "_"

logger = logging.getLogger()

def main():
    global out
    global outExt
    global engineId

    parser = argparse.ArgumentParser(description="The converter that convert from Brat to EMDF (CMU format) , requires at least the input file name/directory/list")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-d","--dir",help="directory of the annotations")
    group.add_argument("-f","--file",help="name of one annotation file")
    group.add_argument("-l","--filelist",help="a file that each line is a file that will be processed")
    parser.add_argument("-o","--out",help="output path, '"+out+"' by default")
    parser.add_argument("-e","--ext",help="output extension, '"+outExt+"' by default")
    parser.add_argument("-i","--eid",help="an engine id that will appears at each line of the output file")

    args = parser.parse_args() 
    stream_handler = logging.StreamHandler(sys.stderr)  
    logger.addHandler(stream_handler)  

    if args.out != None:
        out = args.out
    if args.ext != None:
        outExt = args.ext
    if args.eid != None:
        engineId = args.eid

    #ensure output directory exists
    
    try:
        head,tail = os.path.split(out)
        if head != "":
            os.makedirs(head)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    outFile = open(out+"."+outExt,'w')

    if args.dir != None:
        #parse directory
        for f in os.listdir(args.dir):
            if f.endswith(".ann"):
                parse_annotation_file(args.dir+os.sep+f,outFile)
    elif args.file != None:
        #parse one annotation file
        if args.file.endswith(".ann"):
            parse_annotation_file(args.file,outFile)
    elif args.filelist != None:
        #parse the filelist
        lst = open(args.filelist)
        for line in lst:
            l = line.rstrip()
            parse_annotation_file(l,outFile)

def clear():
    textBounds = {} # all text bounds
    events = {} # all events 
    atts = {} # all attributes 

def span2Text(spans):
    s = ""
    sep = ""
    for span in spans:
        s += sep 
        s += str(span[0])+spanJonier+str(span[1])
        sep = spanSeperator
    return s

def parse_annotation_file(filePath,of):
    if os.path.isfile(filePath):
        f = open(filePath)
        textId = os.path.splitext(os.path.basename(f.name))[0]
        read_all_anno(f)
        
        eids = events.keys()
        eids.sort(key=lambda x: int(x[1:]) )

        of.write(bodMarker+" "+textId+"\n")
        for eid in eids:
            eventType = events[eid][0][0]
            textBoundId = events[eid][0][1]
            att = atts[eid]
            textBound  = textBounds[textBoundId]
            spans = textBound[1]
            text = textBound[2]

            of.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n"%(engineId,textId,eid,span2Text(spans),text,eventType,att["Realis"][1],1))
        of.write(eodMarker+"\n")
        clear()
    else:
        logger.error("Cannot find file specified : %s"%(filePath))

def parse_span(allSpanStr):
    spanStrs = allSpanStr.split(";")
    spans = []
    for spanStr in spanStrs:
        span = spanStr.split()
        spans.append((int(span[0]),int(span[1])))
    return spans

def parse_text_bound(fields):
    if len(fields) != 3:
        logger.error("Incorrect number of fields in a text bound annotation")
    tid = fields[0]
    typeSpan = fields[1].split(" ",1)
    tbType = typeSpan[0]
    spans = parse_span(typeSpan[1])
    text = fields[2]
    return (tid,(tbType,spans,text))

def parse_event(fields):
    eid = fields[0]
    triggerAndRoles = fields[1].split()
    trigger = triggerAndRoles[0].split(":")
    
    roles = []
    for rolesStr in triggerAndRoles[1:]:
        role = rolesStr.split(":")
        roles.append(role)

    return (eid,(trigger,roles))

def parse_attribute(fields):
    aid = fields[0]
    value = fields[1].split()
    attName = value[0]
    targetId = value[1]
    targetValue = True #binary

    if len(value) == 3: #multi-valued
        targetValue = value[2]

    return (aid,targetId,attName,targetValue)

def read_all_anno(f):
    for line in f:
        if line.startswith(noteMarker):
            pass
        fields = line.rstrip().split("\t",2)
        if line.startswith(spanMarker):
            textBound = parse_text_bound(fields)
            textBounds[textBound[0]] = textBound[1]
        if line.startswith(eventMarker):
            event = parse_event(fields)
            events[event[0]]= event[1]
        if line.startswith(attMarker) or line.startswith(attMarkerBack):
            (aid, targetId, attName, targetValue) = parse_attribute(fields) 
            if atts.has_key(targetId):
                atts[targetId][attName] = (aid,targetValue)
            else:
                atts[targetId] = {}
                atts[targetId][attName] = (aid,targetValue)

if __name__ == "__main__":
    main()