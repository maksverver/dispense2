VERSION=0.1.3
NAME=dispense2
DOCS=manual.html project.xsd
SCRIPTS=collect.py dispense.py enact.py host.py participate.py project.py
FILES=$(DOCS) $(SCRIPTS)

all:
	@echo All done.

manual.html: manual.xml
	xsltproc /usr/local/share/xsl/docbook/xhtml/docbook.xsl manual.xml > manual.html

archives: manual.html
	mkdir "dist/$(NAME)"
	cp -R $(FILES) "dist/$(NAME)"
	-rm "dist/$(NAME)-$(VERSION).zip" "dist/$(NAME)-$(VERSION).tar.gz" "dist/$(NAME)-$(VERSION).tar.bz2" 
	cd dist && zip -r "$(NAME)-$(VERSION).zip" $(NAME)
	cd dist && tar cfz "$(NAME)-$(VERSION).tar.gz" $(NAME)
	cd dist && tar cfy "$(NAME)-$(VERSION).tar.bz2" $(NAME)
	rm -R "dist/$(NAME)"

