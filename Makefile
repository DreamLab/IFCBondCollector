PROJECT=ifcbondcollector
VERSION=2.0.0

all:
	@echo "make deb - Generate a deb package"

deb: builddeb

builddeb:
	mkdir -p contrib/deb/etc/diamond/collectors/
	mkdir -p contrib/deb/etc/sudoers.d/
	mkdir -p contrib/deb/usr/share/diamond/collectors/ifcbondcollector/
	cp conf/IFCBondCollector.conf contrib/deb/etc/diamond/collectors/
	cp src/ifcbondcollector.py contrib/deb/usr/share/diamond/collectors/ifcbondcollector/
	cp conf/lldpctl contrib/deb/etc/sudoers.d/
	find contrib/deb/ -type f ! -regex '.*.git.*' ! -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf 'contrib/deb/%P ' | xargs md5sum > contrib/deb/DEBIAN/md5sums

	fakeroot dpkg-deb -b contrib/deb/ ./bin

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -rf `find . -type d -name '*.egg-info'`
	rm -rf dist build htmlcov .tox
