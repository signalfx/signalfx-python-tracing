.PHONY: tools
tools:
	pip install sdist twine[readme_renderer]

.PHONY: build
build:
	python setup.py sdist
	twine check dist/*tar.gz


.PHONY: publish
publish:
	twine upload dist/signalfx-tracing-${VERSION}.tar.gz
