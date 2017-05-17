#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ringo.lib.imexport import Exporter, ExportConfiguration


class RecursiveRelationExporter(Exporter):

    """Recursive Expoert for items of type clazz. After the export has
    finished the exported data will are returned as a dictionary. Each
    key in the dictionary will hold the exported values of the
    configured relations in the export configuration. The items of type
    clazz acn be found in the dict under the key 'root'"""

    def __init__(self, clazz, config):
        self._config
        if config:
            config = ExportConfiguration(config).config
        else:
            config = {"root": None}
        super(RecursiveRelationExporter, self).__init__(clazz,
                                                        fields=config["root"],
                                                        serialized=False,
                                                        config=config)
        self._data = {}

    def perform(self, items):
        export = super(RecursiveRelationExporter, self).perform(items)
        self._iter_export(export, self._config, "root")
        self._remove_duplicates()
        return self._data

    def get_relation_config(self):
        return self._config

    def _iter_export(self, export, relation_config, relation):
        if self._data.get(relation) is None:
            self._data[relation] = []
        for item in export:
            temp = {}
            for field in item:
                if field in relation_config:
                    fields_to_export = relation_config[field]
                    if isinstance(item[field], list) and len(item[field]) > 0:
                        clazz = item[field][0].__class__
                        exporter = Exporter(clazz,
                                            fields_to_export,
                                            serialized=False)
                        self._iter_export(exporter.perform(item[field]),
                                          relation_config,
                                          field)
                    elif item[field] is not None:
                        clazz = item[field]
                        exporter = Exporter(clazz,
                                            fields_to_export,
                                            serialized=False)
                        self._iter_export(exporter.perform([item[field]]),
                                          relation_config,
                                          field)
                else:
                    temp[field] = item[field]
            self._data[relation].append(temp)

    def _remove_duplicates(self):
        for relation in self._data:
            visited = []
            unique = []
            for item in self._data[relation]:
                hashv = hash(unicode(item))
                if hashv not in visited:
                    visited.append(hashv)
                    unique.append(item)
                else:
                    continue
            self._data[relation] = unique
