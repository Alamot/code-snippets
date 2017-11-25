function wrap {
    for i in `seq 0 $1`; do
        echo "$2$i$3"
    done
}

N=2 # Change this accordingly to number of files, that you want to feed to tesseract or export it as a script parameter.

# Uncomment this line if, you're rerunning the script
rm hsk.pffmtable  hsk.shapetable hsk.traineddata hsk.unicharset unicharset output_unicharset font_properties hsk.inttemp hsk.normproto *.tr *.txt

for i in `seq 0 $N`; do
    tesseract hsk.ocrb.exp$i.png hsk.ocrb.exp$i nobatch box.train
done
unicharset_extractor `wrap $N "hsk.ocrb.exp" ".box"`
#set_unicharset_properties -U unicharset -O output_unicharset --script_dir=/usr/share/tessdata/eng.traineddata
echo "ocrb 0 0 0 0 0" > font_properties # tell Tesseract informations about the font
mftraining -F font_properties -U unicharset -O hsk.unicharset `wrap $N "hsk.ocrb.exp" ".tr"`
cntraining `wrap $N "hsk.ocrb.exp" ".tr"`
# rename all files created by mftraing en cntraining, add the prefix hsk.:
    mv inttemp hsk.inttemp
    mv normproto hsk.normproto
    mv pffmtable hsk.pffmtable
    mv shapetable hsk.shapetable
combine_tessdata hsk.
