"""GDTF Share modal operator for Blender UI."""

import bpy
from bpy.types import Operator, Context, PropertyGroup
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty
import os
from bthl.api.gdtf import GDTFShareAPI

# In-memory cache for GDTF fixture files
_gdtf_file_cache = {}


class GDTFPasswordInputModal(Operator):
    """Modal dialog for entering GDTF credentials"""

    bl_idname = "bthl.gdtf_password_input"
    bl_label = "GDTF Share Login"
    bl_options = {"INTERNAL"}

    username: StringProperty(
        name="Username",
        description="GDTF Share account username",
    )
    password: StringProperty(
        name="Password",
        description="GDTF Share account password",
        subtype="PASSWORD",
    )

    def execute(self, context: Context):
        """Attempt login with provided credentials"""
        # Only save username to scene, never save password
        context.scene.gdtf_username = self.username
        
        if GDTFShareToggleModal.login(context, self.username, self.password):
            return {"FINISHED"}
        return {"CANCELLED"}

    def invoke(self, context: Context, event):
        """Show password input dialog"""
        self.username = context.scene.gdtf_username
        return context.window_manager.invoke_props_dialog(self, width=300)


class GDTFShareToggleModal(Operator):
    """Operator for GDTF Share integration"""

    bl_idname = "bthl.gdtf_share_toggle"
    bl_label = "GDTF Share"
    bl_description = "Manage GDTF fixture downloads"
    bl_options = {"REGISTER", "UNDO"}

    # Properties for the operator
    action: StringProperty(
        default="login",
        options={"HIDDEN"}
    )

    # Scene property names
    gdtf_username_prop = "gdtf_username"
    gdtf_logged_in_prop = "gdtf_logged_in"
    gdtf_last_error_prop = "gdtf_last_error"
    gdtf_fixture_count_prop = "gdtf_fixture_count"

    def execute(self, context: Context):
        """Execute login or logout action"""
        if self.action == "logout":
            self.logout(context)
            return {"FINISHED"}
        return {"FINISHED"}

    @staticmethod
    def get_gdtf_username(context: Context) -> str:
        """Get stored GDTF username from scene"""
        return getattr(context.scene, GDTFShareToggleModal.gdtf_username_prop, "")

    @staticmethod
    def get_gdtf_logged_in(context: Context) -> bool:
        """Get GDTF login status"""
        return getattr(context.scene, GDTFShareToggleModal.gdtf_logged_in_prop, False)

    @staticmethod
    def get_gdtf_last_error(context: Context) -> str:
        """Get last GDTF error message"""
        return getattr(context.scene, GDTFShareToggleModal.gdtf_last_error_prop, "")

    @staticmethod
    def get_gdtf_fixture_count(context: Context) -> int:
        """Get count of available fixtures"""
        return getattr(context.scene, GDTFShareToggleModal.gdtf_fixture_count_prop, 0)

    @staticmethod
    def login(context: Context, username: str, password: str) -> bool:
        """Attempt to login to GDTF Share.

        Args:
            username: GDTF Share username
            password: GDTF Share password (NOT stored)

        Returns:
            True if login successful
        """
        if not username or not password:
            context.scene.gdtf_last_error = "Username and password required"
            return False

        try:
            api = GDTFShareAPI()
            api.login(username, password)
            context.scene.gdtf_logged_in = True
            context.scene.gdtf_last_error = ""

            # Try to get fixture list count
            try:
                fixtures = api.get_fixture_list()
                context.scene.gdtf_fixture_count = len(fixtures)
            except Exception as e:
                print(f"Warning: Could not get fixture list: {e}")

            return True
        except Exception as e:
            context.scene.gdtf_logged_in = False
            context.scene.gdtf_last_error = str(e)
            return False

    @staticmethod
    def logout(context: Context) -> None:
        """Logout from GDTF Share."""
        context.scene.gdtf_logged_in = False
        context.scene.gdtf_fixture_count = 0
        context.scene.gdtf_last_error = "Logged out"

    @staticmethod
    def get_fixtures(context: Context) -> list:
        """Get list of available fixtures from GDTF Share.

        Returns:
            List of fixture dictionaries, or empty list if not logged in
        """
        if not GDTFShareToggleModal.get_gdtf_logged_in(context):
            context.scene.gdtf_last_error = "Not logged in to GDTF Share"
            return []

        try:
            api = GDTFShareAPI()
            fixtures = api.get_fixture_list()
            context.scene.gdtf_fixture_count = len(fixtures)
            context.scene.gdtf_last_error = ""
            return fixtures
        except Exception as e:
            context.scene.gdtf_last_error = str(e)
            return []

    @staticmethod
    def register():
        """Register scene properties."""
        # Register fixture result property group
        bpy.utils.register_class(GDTFFixtureResult)
        
        bpy.types.Scene.gdtf_username = StringProperty(
            name="GDTF Username",
            description="GDTF Share account username",
            default="",
        )

        bpy.types.Scene.gdtf_logged_in = BoolProperty(
            name="GDTF Logged In",
            description="GDTF Share login status",
            default=False,
        )

        bpy.types.Scene.gdtf_last_error = StringProperty(
            name="GDTF Last Error",
            description="Last error message from GDTF operations",
            default="",
        )

        bpy.types.Scene.gdtf_fixture_count = IntProperty(
            name="GDTF Fixture Count",
            description="Number of available fixtures",
            default=0,
            min=0,
        )

        bpy.types.Scene.gdtf_search_query = StringProperty(
            name="GDTF Search Query",
            description="Current search query",
            default="",
        )

        bpy.types.Scene.gdtf_search_results = CollectionProperty(
            type=GDTFFixtureResult,
            name="GDTF Search Results",
            description="Results from latest fixture search",
        )

        bpy.types.Scene.gdtf_search_result_index = IntProperty(
            name="GDTF Search Result Index",
            description="Currently selected search result",
            default=0,
            min=0,
        )

        bpy.types.Scene.gdtf_fixture_universe = IntProperty(
            name="GDTF Fixture Universe",
            description="DMX universe for new fixtures",
            default=1,
            min=1,
        )

        bpy.types.Scene.gdtf_fixture_channel = IntProperty(
            name="GDTF Fixture Channel",
            description="DMX channel for new fixtures",
            default=1,
            min=1,
            max=512,
        )

    @staticmethod
    def unregister():
        """Unregister scene properties."""
        properties = [
            GDTFShareToggleModal.gdtf_username_prop,
            GDTFShareToggleModal.gdtf_logged_in_prop,
            GDTFShareToggleModal.gdtf_last_error_prop,
            GDTFShareToggleModal.gdtf_fixture_count_prop,
            "gdtf_search_query",
            "gdtf_search_results",
            "gdtf_search_result_index",
            "gdtf_fixture_universe",
            "gdtf_fixture_channel",
        ]

        for prop in properties:
            if hasattr(bpy.types.Scene, prop):
                delattr(bpy.types.Scene, prop)
        
        # Unregister fixture result property group
        try:
            bpy.utils.unregister_class(GDTFFixtureResult)
        except RuntimeError:
            pass


class GDTFFixtureResult(PropertyGroup):
    """Property group for storing search result fixture data."""
    
    rid: IntProperty(name="Revision ID")
    fixture: StringProperty(name="Fixture Name")
    manufacturer: StringProperty(name="Manufacturer")
    rating: IntProperty(name="Rating", min=0, max=5)
    modes: StringProperty(name="Modes Count")
    filesize: IntProperty(name="File Size")
    universe: IntProperty(name="Universe", default=1, min=1)
    channel: IntProperty(name="Channel", default=1, min=1, max=512)


class GDTFSearchModal(Operator):
    """Modal dialog for searching GDTF fixtures."""

    bl_idname = "bthl.gdtf_search"
    bl_label = "Search GDTF Fixtures"
    bl_options = {"INTERNAL"}

    search_query: StringProperty(
        name="Search",
        description="Search by fixture name or manufacturer",
    )

    def execute(self, context: Context):
        """Perform fixture search."""
        if not context.scene.gdtf_logged_in:
            context.scene.gdtf_last_error = "Not logged in to GDTF Share"
            return {"CANCELLED"}

        try:
            api = GDTFShareAPI()
            fixtures = api.get_fixture_list()
            
            # Clear previous results
            context.scene.gdtf_search_results.clear()
            
            # Perform search
            results = api.search_fixtures(self.search_query, fixtures)
            
            # Add results to collection
            for fixture in results:
                result = context.scene.gdtf_search_results.add()
                result.rid = fixture.get("rid", 0)
                result.fixture = fixture.get("fixture", "")
                result.manufacturer = fixture.get("manufacturer", "")
                try:
                    result.rating = int(fixture.get("rating", 0)) if fixture.get("rating") else 0
                except (ValueError, TypeError):
                    result.rating = 0
                result.modes = str(len(fixture.get("modes", [])))
                result.filesize = fixture.get("filesize", 0)
                result.universe = context.scene.gdtf_fixture_universe
                result.channel = context.scene.gdtf_fixture_channel
            
            context.scene.gdtf_last_error = f"Found {len(results)} fixtures"
            context.scene.gdtf_search_result_index = 0
            
            return {"FINISHED"}
        except Exception as e:
            context.scene.gdtf_last_error = f"Search failed: {str(e)}"
            context.scene.gdtf_search_results.clear()
            return {"CANCELLED"}

    def invoke(self, context: Context, event):
        """Show search dialog."""
        self.search_query = context.scene.gdtf_search_query
        return context.window_manager.invoke_props_dialog(self, width=400)


class GDTFDownloadResultModal(Operator):
    """Add a selected search result fixture to the scene."""

    bl_idname = "bthl.gdtf_add_fixture"
    bl_label = "Add Fixture to Scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        """Add the selected fixture from search results to the scene."""
        if not context.scene.gdtf_search_results:
            context.scene.gdtf_last_error = "No search results to add"
            return {"CANCELLED"}

        idx = context.scene.gdtf_search_result_index
        if idx >= len(context.scene.gdtf_search_results):
            context.scene.gdtf_last_error = "Invalid result selection"
            return {"CANCELLED"}

        result = context.scene.gdtf_search_results[idx]
        
        try:
            # Load GDTF file into memory cache
            api = GDTFShareAPI()
            gdtf_data = api.download_fixture_to_bytes(result.rid)
            
            # Cache the GDTF file data in memory
            cache_key = f"{result.manufacturer}_{result.fixture}_{result.rid}"
            _gdtf_file_cache[cache_key] = gdtf_data
            
            # Create an empty object at 3D cursor location
            location = context.scene.cursor.location
            
            # Create empty object as fixture representation
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
            fixture_obj = context.active_object
            
            # Name the object after the fixture with universe and channel
            fixture_obj.name = f"U{result.universe}_C{result.channel}_{result.manufacturer}_{result.fixture}"
            
            # Store fixture metadata as custom properties
            fixture_obj["gdtf_rid"] = result.rid
            fixture_obj["gdtf_fixture"] = result.fixture
            fixture_obj["gdtf_manufacturer"] = result.manufacturer
            fixture_obj["gdtf_rating"] = result.rating
            fixture_obj["gdtf_modes"] = result.modes
            fixture_obj["gdtf_filesize"] = result.filesize
            fixture_obj["gdtf_universe"] = result.universe
            fixture_obj["gdtf_channel"] = result.channel
            fixture_obj["gdtf_cache_key"] = cache_key
            
            context.scene.gdtf_last_error = f"Added: U{result.universe}_C{result.channel} - {result.fixture}"
            return {"FINISHED"}
        except Exception as e:
            context.scene.gdtf_last_error = f"Failed to add fixture: {str(e)}"
            return {"CANCELLED"}


class GDTFRefreshModal(Operator):
    """Refresh the fixture list and show all available fixtures."""

    bl_idname = "bthl.gdtf_refresh"
    bl_label = "Refresh Fixtures"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        """Refresh and display all available fixtures."""
        if not context.scene.gdtf_logged_in:
            context.scene.gdtf_last_error = "Not logged in to GDTF Share"
            return {"CANCELLED"}

        try:
            api = GDTFShareAPI()
            fixtures = api.get_fixture_list()
            
            # Clear previous results
            context.scene.gdtf_search_results.clear()
            context.scene.gdtf_search_query = ""
            
            # Add all fixtures to results
            for fixture in fixtures:
                result = context.scene.gdtf_search_results.add()
                result.rid = fixture.get("rid", 0)
                result.fixture = fixture.get("fixture", "")
                result.manufacturer = fixture.get("manufacturer", "")
                try:
                    result.rating = int(fixture.get("rating", 0)) if fixture.get("rating") else 0
                except (ValueError, TypeError):
                    result.rating = 0
                result.modes = str(len(fixture.get("modes", [])))
                result.filesize = fixture.get("filesize", 0)
                result.universe = context.scene.gdtf_fixture_universe
                result.channel = context.scene.gdtf_fixture_channel
            
            context.scene.gdtf_fixture_count = len(fixtures)
            context.scene.gdtf_last_error = f"Loaded all {len(fixtures)} fixtures"
            context.scene.gdtf_search_result_index = 0
            
            return {"FINISHED"}
        except Exception as e:
            context.scene.gdtf_last_error = f"Refresh failed: {str(e)}"
            context.scene.gdtf_search_results.clear()
            return {"CANCELLED"}
