ARCHIVE_DIRECTORY=~/Desktop/
FILESCHEME=store*.tgs
FILESCHEME_MINIMAL=ministore*.tgs
FILESCHEME_ALL=*.tgs
SCRIPT=../analyze_artifacts_tagstore.py

.PHONY: clean standard minimal huge quiet

clean:
	-rm *.csv 
	-rm *.png
	-rm Archive.zip

standard: clean
	$(SCRIPT) -v $(FILESCHEME)

minimal: clean
	$(SCRIPT) -v $(FILESCHEME_MINIMAL)

huge: clean
	$(SCRIPT) -v $(FILESCHEME_ALL)

archive: huge
	-zip $(ARCHIVE_DIRECTORY)Archive.zip *.csv *.png
