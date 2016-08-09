# -*- coding: utf-8 -*-
#


# Make '_' a no-op so we can scrape strings
def _(text):
    return text


class Constants(object):
    ALLOWED_ZONE_ALIGNMENT = ['left', 'right', 'center']
    DEFAULT_ZONE_ALIGNMENT = 'center'


class StateMigration(object):
    """
    Helper class to apply zone data and item state migrations
    """

    @classmethod
    def _apply_migration(cls, obj, migrations):
        """
        Applies migrations sequentially to a copy of an `obj`, to avoid updating actual data
        """
        tmp = obj.copy()
        for method in migrations:
            tmp = method(tmp)

        return tmp

    @classmethod
    def apply_zone_migrations(cls, zone):
        """
        Applies zone migrations
        """
        migrations = (cls._zone_v1_to_v2, cls._zone_v2_to_v2p1)

        return cls._apply_migration(zone, migrations)

    @classmethod
    def apply_item_state_migrations(cls, item_state):
        """
        Applies item_state migrations
        """
        migrations = (cls._item_state_v1_to_v1p5, cls._item_state_v1p5_to_v2, cls._item_state_v1p5_to_v2p1)

        return cls._apply_migration(item_state, migrations)

    @classmethod
    def _zone_v1_to_v2(cls, zone):
        """
        Migrates zone data from v1.0 format to v2.0 format.

        Changes:
        * v1 used zone "title" as UID, while v2 have "uid" property
        * "id" and "index" properties are no longer used

        In: {'id': 1, 'index': 2, 'title': "Zone", ...}
        Out: {'uid': "Zone", ...}
        """
        if "uid" not in zone:
            zone["uid"] = zone.get("title")
        zone.pop("id", None)
        zone.pop("index", None)

        return zone

    @classmethod
    def _zone_v2_to_v2p1(cls, zone):
        """
        Migrates zone data from v2.0 to v2.5

        Changes:
        * Removed "none" zone alignment; default align is "center"

        In: {
            'uid': "Zone", "align": "none",
            "x_percent": "10%", "y_percent": "10%", "width_percent": "10%", "height_percent": "10%"
        }
        Out: {
            'uid': "Zone", "align": "center",
            "x_percent": "10%", "y_percent": "10%", "width_percent": "10%", "height_percent": "10%"
        }
        """
        if zone.get('align', None) not in Constants.ALLOWED_ZONE_ALIGNMENT:
            zone['align'] = Constants.DEFAULT_ZONE_ALIGNMENT

        return zone

    @classmethod
    def _item_state_v1_to_v1p5(cls, item):
        """
        Migrates item_state from v1.0 to v1.5

        Changes:
        * Item state is now a dict instead of tuple

        In: ('100px', '120px')
        Out: {'top': '100px', 'left': '120px'}
        """
        if isinstance(item, dict):
            return item
        else:
            return {'top': item[0], 'left': item[1]}

    @classmethod
    def _item_state_v1p5_to_v2(cls, item):
        """
        Migrates item_state from v1.5 to v2.0

        Changes:
        * Item placement attributes switched from absolute (left-top) to relative (x_percent-y_pecrent) units

        In: {'zone': 'Zone", 'correct': True, 'top': '100px', 'left': '120px'}
        Out: {'zone': 'Zone", 'correct': True, 'top': '100px', 'left': '120px'}
        """
        # Conversion can't be made as parent dimensions are unknown to python - converted in JS
        # Since 2.5 JS this conversion became unnecesary, so it was removed from JS code
        return item

    @classmethod
    def _item_state_v1p5_to_v2p1(cls, item):
        """
        Migrates item_state from v1.5 to v2.5

        Changes:
        * Removed "none" zone alignment - remove old "absolute" placement attributes

        In: {'zone': 'Zone", 'correct': True, 'top': '100px', 'left': '120px', 'absolute': true}
        Out: {'zone': 'Zone", 'correct': True}

        In: {'zone': 'Zone", 'correct': True, 'x_percent': '90%', 'y_percent': '20%'}
        Out: {'zone': 'Zone", 'correct': True}
        """
        attributes_to_remove = ['x_percent', 'y_percent', 'left', 'top', 'absolute']
        for attribute in attributes_to_remove:
            del[attribute]

        return item
