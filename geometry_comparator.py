# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeometryComparator
                                 A QGIS plugin
 Detects changes between two vector layers (Polygon, Line or Point) by comparing features based on a Unique ID field and their geometries, identifying Added, Deleted, and Modified features with high accuracy
                              -------------------
        begin                : 2025-06-10
        git sha              : $Format:%H$
        copyright            : (C) 2025 by Anustup Jana
        email                : anustupjana21@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis import processing
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterEnum,
    QgsProcessingException,
    QgsVectorLayer,
    QgsFeatureSink,
    QgsFeature,
    QgsFields,
    QgsWkbTypes,
    QgsProcessingContext,
    QgsProject,
    QgsProcessingFeatureSource,
    QgsFeatureRequest,
    QgsProcessingProvider,
    QgsGeometry,
    QgsPointXY,
    QgsApplication
)
import os.path

# Initialize Qt resources from file resources.py
from .resources import *

class CompareFeaturesAlgorithm(QgsProcessingAlgorithm):
    OLD_LAYER = 'OLD_LAYER'
    NEW_LAYER = 'NEW_LAYER'
    ID_FIELD = 'ID_FIELD'
    MODIFIED_OUTPUT = 'MODIFIED_OUTPUT'
    ADDED_OUTPUT = 'ADDED_OUTPUT'
    DELETED_OUTPUT = 'DELETED_OUTPUT'
    GEOMETRY_TYPE = 'GEOMETRY_TYPE'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterEnum(
                self.GEOMETRY_TYPE,
                'Geometry Type',
                options=['Polygon', 'Line', 'Point'],
                defaultValue=0,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.OLD_LAYER,
                'Old Layer',
                [QgsProcessing.TypeVectorAnyGeometry],
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.NEW_LAYER,
                'New Layer',
                [QgsProcessing.TypeVectorAnyGeometry],
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.ID_FIELD,
                'Unique ID Field',
                defaultValue='id',
                type=QgsProcessingParameterField.Any,
                parentLayerParameterName=self.OLD_LAYER,
                allowMultiple=False,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.MODIFIED_OUTPUT,
                'Modified Features',
                QgsProcessing.TypeVectorAnyGeometry
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.ADDED_OUTPUT,
                'Added Features',
                QgsProcessing.TypeVectorAnyGeometry
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.DELETED_OUTPUT,
                'Deleted Features',
                QgsProcessing.TypeVectorAnyGeometry
            )
        )

    def prepareAlgorithm(self, parameters, context, feedback):
        geometry_index = self.parameterAsEnum(parameters, self.GEOMETRY_TYPE, context)
        self.geometry_type = ['Polygon', 'Line', 'Point'][geometry_index]
        self.geometry_map = {
            "Polygon": (QgsProcessing.TypeVectorPolygon, QgsWkbTypes.Polygon, 2),
            "Line": (QgsProcessing.TypeVectorLine, QgsWkbTypes.LineString, 1),
            "Point": (QgsProcessing.TypeVectorPoint, QgsWkbTypes.Point, 0)
        }
        self.tolerance = 0.000001 if self.geometry_type == "Point" else 0
        return True

    def processAlgorithm(self, parameters, context, feedback):
        try:
            old_source = self.parameterAsSource(parameters, self.OLD_LAYER, context)
            new_source = self.parameterAsSource(parameters, self.NEW_LAYER, context)
            id_field = self.parameterAsString(parameters, self.ID_FIELD, context)

            if old_source is None:
                raise QgsProcessingException(f"Old {self.geometry_type} Layer is not provided.")
            if new_source is None:
                raise QgsProcessingException(f"New {self.geometry_type} Layer is not provided.")

            old_layer = old_source.materialize(QgsFeatureRequest())
            new_layer = new_source.materialize(QgsFeatureRequest())

            feedback.pushInfo(f"Old Layer: {old_layer.name()}, Feature Count: {old_layer.featureCount()}, CRS: {old_layer.crs().authid()}")
            feedback.pushInfo(f"New Layer: {new_layer.name()}, Feature Count: {new_layer.featureCount()}, CRS: {new_layer.crs().authid()}")

            expected_geometry = self.geometry_map[self.geometry_type][2]
            if old_layer.geometryType() != expected_geometry:
                raise QgsProcessingException(f"Old layer is not a {self.geometry_type.lower()} layer. Geometry Type: {old_layer.geometryType()}")
            if new_layer.geometryType() != expected_geometry:
                raise QgsProcessingException(f"New layer is not a {self.geometry_type.lower()} layer. Geometry Type: {new_layer.geometryType()}")

            if id_field not in old_layer.fields().names():
                raise QgsProcessingException(f"ID field '{id_field}' not found in Old {self.geometry_type} Layer. Fields: {old_layer.fields().names()}")
            if id_field not in new_layer.fields().names():
                raise QgsProcessingException(f"ID field '{id_field}' not found in New {self.geometry_type} Layer. Fields: {new_layer.fields().names()}")

            if old_layer.featureCount() == 0:
                feedback.pushInfo(f"Old {self.geometry_type} Layer is empty. No features to process.")
            if new_layer.featureCount() == 0:
                feedback.pushInfo(f"New {self.geometry_type} Layer is empty. No features to process.")

            wkb_type = self.geometry_map[self.geometry_type][1]
            modified_fields = new_layer.fields()
            (modified_sink, modified_dest_id) = self.parameterAsSink(
                parameters, self.MODIFIED_OUTPUT, context,
                modified_fields, wkb_type, new_layer.crs()
            )
            added_fields = new_layer.fields()
            (added_sink, added_dest_id) = self.parameterAsSink(
                parameters, self.ADDED_OUTPUT, context,
                added_fields, wkb_type, new_layer.crs()
            )
            deleted_fields = old_layer.fields()
            (deleted_sink, deleted_dest_id) = self.parameterAsSink(
                parameters, self.DELETED_OUTPUT, context,
                deleted_fields, wkb_type, old_layer.crs()
            )

            context.addLayerToLoadOnCompletion(
                modified_dest_id,
                QgsProcessingContext.LayerDetails(f'Modified {self.geometry_type}s', QgsProject.instance(), self.MODIFIED_OUTPUT)
            )
            context.addLayerToLoadOnCompletion(
                added_dest_id,
                QgsProcessingContext.LayerDetails(f'Added {self.geometry_type}s', QgsProject.instance(), self.ADDED_OUTPUT)
            )
            context.addLayerToLoadOnCompletion(
                deleted_dest_id,
                QgsProcessingContext.LayerDetails(f'Deleted {self.geometry_type}s', QgsProject.instance(), self.DELETED_OUTPUT)
            )

            old_features = {}
            invalid_old_ids = 0
            for f in old_layer.getFeatures():
                if f[id_field] is None or f[id_field] == '':
                    invalid_old_ids += 1
                    continue
                old_features[f[id_field]] = f
            new_features = {}
            invalid_new_ids = 0
            for f in new_layer.getFeatures():
                if f[id_field] is None or f[id_field] == '':
                    invalid_new_ids += 1
                    continue
                new_features[f[id_field]] = f

            if invalid_old_ids > 0:
                feedback.pushInfo(f"Skipped {invalid_old_ids} features in Old Layer with null or empty IDs.")
            if invalid_new_ids > 0:
                feedback.pushInfo(f"Skipped {invalid_new_ids} features in New Layer with null or empty IDs.")

            old_ids = set(old_features.keys())
            new_ids = set(new_features.keys())
            common_ids = old_ids & new_ids
            potential_added_ids = new_ids - old_ids
            potential_deleted_ids = old_ids - new_ids

            matched_by_geometry = {}
            unmatched_old = []
            unmatched_new = []

            for old_id in potential_deleted_ids:
                old_feature = old_features[old_id]
                old_geom = old_feature.geometry()
                if old_geom.isNull() or not old_geom.isGeosValid():
                    feedback.pushInfo(f"Skipped old feature ID {old_id} due to null or invalid geometry.")
                    unmatched_old.append(old_id)
                    continue
                matched = False
                for new_id in potential_added_ids:
                    new_feature = new_features[new_id]
                    new_geom = new_feature.geometry()
                    if new_geom.isNull() or not new_geom.isGeosValid():
                        continue
                    if self.geometry_type == "Point":
                        if old_geom.distance(new_geom) <= self.tolerance:
                            matched_by_geometry[new_id] = old_id
                            matched = True
                            break
                    else:
                        if old_geom.equals(new_geom):
                            matched_by_geometry[new_id] = old_id
                            matched = True
                            break
                if not matched:
                    unmatched_old.append(old_id)

            unmatched_new = [id for id in potential_added_ids if id not in matched_by_geometry]

            added_ids = unmatched_new
            deleted_ids = unmatched_old
            modified_ids = []

            for id in common_ids:
                old_feature = old_features[id]
                new_feature = new_features[id]
                old_geom = old_feature.geometry()
                new_geom = new_feature.geometry()
                if old_geom.isNull() or new_geom.isNull():
                    feedback.pushInfo(f"Skipped feature ID {id} due to null geometry.")
                    continue
                if not old_geom.isGeosValid() or not new_geom.isGeosValid():
                    feedback.pushInfo(f"Skipped feature ID {id} due to invalid geometry.")
                    continue
                if self.geometry_type == "Point":
                    if old_geom.distance(new_geom) > self.tolerance:
                        modified_ids.append(id)
                else:
                    if not old_geom.equals(new_geom):
                        modified_ids.append(id)

            for new_id, old_id in matched_by_geometry.items():
                old_feature = old_features[old_id]
                new_feature = new_features[new_id]
                old_geom = old_feature.geometry()
                new_geom = new_feature.geometry()
                if self.geometry_type == "Point":
                    if old_geom.distance(new_geom) > self.tolerance:
                        modified_ids.append(new_id)
                else:
                    if not old_geom.equals(new_geom):
                        modified_ids.append(new_id)

            feedback.pushInfo(f"Found {len(added_ids)} added IDs, {len(deleted_ids)} deleted IDs, {len(modified_ids)} modified IDs.")

            total_steps = len(added_ids) + len(deleted_ids) + len(modified_ids)
            if total_steps == 0:
                feedback.pushInfo("No differences found between layers. Output layers will be empty.")
                return {
                    self.MODIFIED_OUTPUT: modified_dest_id,
                    self.ADDED_OUTPUT: added_dest_id,
                    self.DELETED_OUTPUT: deleted_dest_id
                }
            current_step = 0

            added_count = 0
            for id in added_ids:
                if feedback.isCanceled():
                    raise QgsProcessingException("Processing canceled by user.")
                feature = new_features[id]
                if feature.geometry().isNull() or not feature.geometry().isGeosValid():
                    feedback.pushInfo(f"Skipped added feature ID {id} due to null or invalid geometry.")
                    continue
                added_sink.addFeature(feature, QgsFeatureSink.FastInsert)
                added_count += 1
                current_step += 1
                feedback.setProgress(100 * current_step / total_steps)

            deleted_count = 0
            for id in deleted_ids:
                if feedback.isCanceled():
                    raise QgsProcessingException("Processing canceled by user.")
                feature = old_features[id]
                if feature.geometry().isNull() or not feature.geometry().isGeosValid():
                    feedback.pushInfo(f"Skipped deleted feature ID {id} due to null or invalid geometry.")
                    continue
                deleted_sink.addFeature(feature, QgsFeatureSink.FastInsert)
                deleted_count += 1
                current_step += 1
                feedback.setProgress(100 * current_step / total_steps)

            modified_count = 0
            for id in modified_ids:
                if feedback.isCanceled():
                    raise QgsProcessingException("Processing canceled by user.")
                feature = new_features[id]
                if feature.geometry().isNull() or not feature.geometry().isGeosValid():
                    continue
                modified_sink.addFeature(feature, QgsFeatureSink.FastInsert)
                modified_count += 1
                current_step += 1
                feedback.setProgress(100 * current_step / total_steps)

            feedback.pushInfo(f"Processed {added_count} added, {deleted_count} deleted, and {modified_count} modified {self.geometry_type.lower()}s.")

            return {
                self.MODIFIED_OUTPUT: modified_dest_id,
                self.ADDED_OUTPUT: added_dest_id,
                self.DELETED_OUTPUT: deleted_dest_id
            }

        except Exception as e:
            raise QgsProcessingException(f"An error occurred: {str(e)}")

    def name(self):
        return 'geometrycomparator'

    def displayName(self):
        return 'Geometry Comparator'

    def group(self):
        return 'Vector Analysis'

    def groupId(self):
        return 'vectoranalysis'

    def createInstance(self):
        return CompareFeaturesAlgorithm()

class GeometryComparatorProvider(QgsProcessingProvider):
    def __init__(self):
        super().__init__()

    def id(self):
        return 'geometrycomparator'

    def name(self):
        return 'Geometry Comparator'

    def loadAlgorithms(self):
        self.addAlgorithm(CompareFeaturesAlgorithm())

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icon.png'))

class GeometryComparator:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeometryComparator_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&Geometry Comparator')
        self.first_start = True
        self.provider = None
        self.toolbar_action = None

    def tr(self, message):
        return QCoreApplication.translate('GeometryComparator', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar_action = action
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)
        return action

    def initProcessing(self):
        self.provider = GeometryComparatorProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        # Clear any existing actions to prevent duplicates
        self.unload()

        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.add_action(
            icon_path,
            text=self.tr(u'Geometry Comparator'),
            callback=self.run,
            parent=self.iface.mainWindow(),
            status_tip='Compare two polygon, line, and point layers to find added, deleted, and modified geometry')

        self.initProcessing()
        self.first_start = False

    def unload(self):
        # Remove all actions from toolbar and menu
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Geometry Comparator'),
                action)
            self.iface.removeToolBarIcon(action)
        self.actions.clear()

        # Clear toolbar action reference
        self.toolbar_action = None

        # Remove processing provider
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None

    def run(self):
        """Run method that performs all the real work."""
        processing.execAlgorithmDialog('geometrycomparator:geometrycomparator', {})

        # Show success message
        self.iface.messageBar().pushMessage(
            "Success",
            "Changes geometry successfully added",
            level=3,  # Qgis.Info
            duration=5
        )