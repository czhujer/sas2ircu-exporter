IMAGE = registry.mallgroup.com/cc/sas2ircu-exporter
VERSION = 0.1

.PHONY: _
_: build publish

.PHONY: build
build:
	docker build -t $(IMAGE):$(VERSION) .

.PHONY: publish
publish:
	docker push $(IMAGE):$(VERSION)
