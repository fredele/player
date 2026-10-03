from flask_restx import Resource


def register_swagger_routes(api, ns):
    """Register RESTX resources for the public API endpoints."""

    from main import (
        ClearQueriesCache,
        Commands_Get,
        Commands_Run,
        CurrentPosition,
        Display_Covers,
        Display_Files,
        Display_Group,
        GetAllValuesOfField,
        Get_Settings,
        Goodbye,
        Info,
        Lang_Get,
        LibrarySearch,
        Library_Backup,
        Library_Restore,
        Library_Scan_Music_Update_Folders,
        Library_Scan_Status,
        Library_Reimport,
        Library_import,
        Next,
        Output_Get,
        Output_HW_Params,
        Output_Set,
        Play,
        Playlists_Get,
        Previous,
        Restartqueue,
        Set,
        Set_Settings,
        Set_Tag,
        State,
        Stop,
        TrackInfo,
        Upnp_Reload,
        Volume_Get,
        Volume_Set,
        clear_queue,
        cover,
        create_indexes,
        dsp_get,
        dsp_set,
        find,
        findfiles,
        get_assets,
        get_files_list,
        get_file,
        get_file2,
        get_playlist,
        get_podcasts,
        get_players,
        get_queue,
        get_radio,
        login,
        menu,
        parse_podcast,
        pulse_outs,
        pulse_set_out,
        queue_add,
        queue_delete,
        queue_move,
        radiomode,
        ripcd,
        save_menu,
        save_outputs,
        save_players,
        send_ip,
        set__player,
        shutdown,
        stats,
        test,
        thumb,
        thumb_epoch,
        transcodedfile,
        transcodedfile_query_legacy,
        upload_file,
        zipdirhash,
    )

    @ns.route("/test")
    class TestResource(Resource):
        @ns.doc(summary="Simple health check", description="Simple health check")
        def get(self):
            return test()

    @ns.route("/Players/Get")
    class PlayersGetResource(Resource):
        @ns.doc(summary="List configured players", description="Returns the list of configured players and their current metadata.")
        def get(self):
            return get_players()

    @ns.route("/Players/Set")
    class PlayersSetResource(Resource):
        @ns.doc(summary="Save players configuration", description="Persists the players configuration sent by the client.")
        def post(self):
            return save_players()

    @ns.route("/Player/State")
    class PlayerStateResource(Resource):
        @ns.doc(summary="Get current player state", description="Returns the active player state and related playback status.")
        def get(self):
            return State()

    @ns.route("/Player/CurrentTrack")
    class CurrentTrackResource(Resource):
        @ns.doc(summary="Get current track metadata", description="Returns the metadata of the track currently playing.")
        def get(self):
            return Info()

    @ns.route("/Player/CurrentPosition")
    class CurrentPositionResource(Resource):
        @ns.doc(summary="Get current playback position", description="Returns the current playback position and timing information.")
        def get(self):
            return CurrentPosition()

    @ns.route("/SetPlayer/<id>")
    class SetPlayerResource(Resource):
        @ns.doc(summary="Select the active player", description="Activates the player matching the provided identifier.", params={"id": "Player identifier to activate"})
        def get(self, id):
            return set__player(id)

    @ns.route("/Transcode/<player_id>/<path:filename>")
    class TranscodeFileResource(Resource):
        @ns.doc(
            summary="Transcode and stream an audio file",
            description="Transcodes and streams the given media file for the specified player.",
            params={
                "player_id": "Player identifier used for transcoding",
                "filename": "File name or relative path to transcode and stream"
            }
        )
        def get(self, player_id, filename):
            return transcodedfile(player_id, filename)

    @ns.route("/Transcode/<path:fileid>")
    class TranscodeLegacyFileResource(Resource):
        @ns.doc(summary="Legacy transcode route", description="Transcodes a legacy media identifier or path using the legacy endpoint format.", params={"fileid": "Legacy file identifier or media path"})
        def get(self, fileid):
            return transcodedfile_query_legacy(fileid)

    @ns.route("/Zip/<dirhash>")
    class ZipDirhashResource(Resource):
        @ns.doc(summary="Stream a directory as zip", description="Returns the content of the referenced directory as a ZIP archive.", params={"dirhash": "Directory hash identifier"})
        def get(self, dirhash):
            return zipdirhash(dirhash)

    @ns.route("/Pulseaudio/Outputs")
    class PulseOutputsResource(Resource):
        @ns.doc(summary="List PulseAudio outputs", description="Lists the available PulseAudio outputs and their current status.")
        def get(self):
            return pulse_outs()

    @ns.route("/Pulseaudio/SetOutput")
    class PulseSetOutputResource(Resource):
        @ns.doc(summary="Move the player to a specific PulseAudio output", description="Switches the current player to the selected PulseAudio output.")
        def get(self):
            return pulse_set_out()

    @ns.route("/<dirhash>/<filename>")
    class FileListingResource(Resource):
        @ns.doc(summary="List or serve a file by dirhash", description="Resolves a directory hash and optionally serves the requested file from that collection.", params={"dirhash": "Directory hash identifier", "filename": "Target file name or file path"})
        def get(self, dirhash, filename):
            return file_listing(dirhash, filename)

    @ns.route("/Player/TrackInfo")
    class TrackInfoResource(Resource):
        @ns.doc(summary="Get track display information", description="Returns the display-ready track information for the current playback context.")
        def get(self):
            return TrackInfo()

    @ns.route("/Player/Next")
    class PlayerNextResource(Resource):
        @ns.doc(summary="Skip to the next track", description="Moves playback to the next item in the current queue.")
        def get(self):
            return Next()

    @ns.route("/Player/Previous")
    class PlayerPreviousResource(Resource):
        @ns.doc(summary="Go to the previous track", description="Moves playback back to the previous item in the current queue.")
        def get(self):
            return Previous()

    @ns.route("/Player/Seek/Set")
    class PlayerSeekSetResource(Resource):
        @ns.doc(summary="Seek in the current track", description="Seeks to the requested playback position in the current track.")
        def get(self):
            return Set()

    @ns.route("/Player/RestartQueue")
    class PlayerRestartQueueResource(Resource):
        @ns.doc(summary="Restart the current player queue", description="Restarts the current played queue from its beginning.")
        def get(self):
            return Restartqueue()

    @ns.route("/Player/Volume/Get")
    class PlayerVolumeGetResource(Resource):
        @ns.doc(summary="Get player volume", description="Returns the current player volume level.")
        def get(self):
            return Volume_Get()

    @ns.route("/Player/Volume/Set")
    class PlayerVolumeSetResource(Resource):
        @ns.doc(summary="Set player volume", description="Sets the player volume to the requested value.")
        def get(self):
            return Volume_Set()

    @ns.route("/Player/Play")
    class PlayerPlayResource(Resource):
        @ns.doc(summary="Play or pause the current track", description="Toggles playback or resumes the current track depending on the player state.")
        def get(self):
            return Play()

    @ns.route("/Player/Stop")
    class PlayerStopResource(Resource):
        @ns.doc(summary="Stop playback", description="Stops the current playback immediately.")
        def get(self):
            return Stop()

    @ns.route("/Player/Radio")
    class PlayerRadioResource(Resource):
        @ns.doc(summary="Play a radio selection", description="Starts or switches the player to the chosen radio source.")
        def get(self):
            return radiomode()

    @ns.route("/Player/DSP/Get")
    class PlayerDSPGetResource(Resource):
        @ns.doc(summary="Get DSP parameters", description="Returns the current DSP configuration and tuning values.")
        def get(self):
            return dsp_get()

    @ns.route("/Player/DSP/Set")
    class PlayerDSPSetResource(Resource):
        @ns.doc(summary="Set DSP parameters", description="Updates the DSP configuration values sent by the client.")
        def get(self):
            return dsp_set()

    @ns.route("/Player/Outputs/Get")
    class OutputsGetResource(Resource):
        @ns.doc(summary="Get outputs list", description="Returns the list of configured audio outputs.")
        def get(self):
            return Output_Get()

    @ns.route("/Outputs/Set")
    class OutputsSetResource(Resource):
        @ns.doc(summary="Load outputs configuration", description="Saves the output configuration received from the client.")
        def post(self):
            return save_outputs()

    @ns.route("/Player/Output/Set")
    class OutputSetResource(Resource):
        @ns.doc(summary="Set the active player output", description="Changes the active audio output for the current player.")
        def get(self):
            return Output_Set()

    @ns.route("/Player/Lang/Get")
    class LanguageGetResource(Resource):
        @ns.doc(summary="Get language configuration", description="Returns the current language configuration used by the application.")
        def get(self):
            return Lang_Get()

    @ns.route("/Player/Output/GetParams")
    class OutputParamsResource(Resource):
        @ns.doc(summary="Get hardware output parameters", description="Returns the hardware-related output parameters for the current device.")
        def get(self):
            return Output_HW_Params()

    @ns.route("/Queue/Get")
    class QueueGetResource(Resource):
        @ns.doc(summary="Get the current queue", description="Returns the items currently queued for playback.")
        def get(self):
            return get_queue()

    @ns.route("/Queue/Clear")
    class QueueClearResource(Resource):
        @ns.doc(summary="Clear the current queue", description="Removes all items from the current playback queue.")
        def get(self):
            return clear_queue()

    @ns.route("/Queue/Delete")
    class QueueDeleteResource(Resource):
        @ns.doc(summary="Delete one queue item", description="Deletes a specific item from the current queue.")
        def get(self):
            return queue_delete()

    @ns.route("/Queue/Move")
    class QueueMoveResource(Resource):
        @ns.doc(summary="Move a queue item", description="Moves a queue item to a new position in the current queue.")
        def get(self):
            return queue_move()

    @ns.route("/Queue/Add")
    class QueueAddResource(Resource):
        @ns.doc(summary="Add items to the queue", description="Adds one or more media items to the current playback queue.")
        def get(self):
            return queue_add()

    @ns.route("/Library/Search")
    class LibrarySearchResource(Resource):
        @ns.doc(summary="Search the library", description="Searches the media library using the provided query.")
        def get(self):
            return LibrarySearch()

    @ns.route("/Library/Scan/Status")
    class LibraryScanStatusResource(Resource):
        @ns.doc(summary="Get the current library scan status", description="Returns the current progress and state of the library scan operation.")
        def get(self):
            return Library_Scan_Status()

    @ns.route("/Library/Scan/Music")
    class LibraryScanMusicResource(Resource):
        @ns.doc(summary="Start a library scan", description="Starts a full library scan and refresh of the media index.")
        def get(self):
            return Library_Scan_Music_Update_Folders()

    @ns.route("/Library/Import")
    @ns.route("/Library/Scan/Import")
    class LibraryImportResource(Resource):
        @ns.doc(summary="Import a folder into the library", description="Imports the specified folder into the media library.")
        def get(self):
            return Library_import()

    @ns.route("/Library/Reimport")
    @ns.route("/Library/Scan/Reimport")
    class LibraryReimportResource(Resource):
        @ns.doc(summary="Reimport a library subset", description="Reimports the selected library subset or updated media collection.")
        def get(self):
            return Library_Reimport()

    @ns.route("/Library/CreateIndexes")
    class LibraryCreateIndexesResource(Resource):
        @ns.doc(summary="Create library indexes", description="Builds or refreshes the library indexes used by search and browsing.")
        def get(self):
            return create_indexes()

    @ns.route("/Library/Radio/Get")
    class LibraryRadioGetResource(Resource):
        @ns.doc(summary="Get radio stations", description="Returns the configured radio stations available in the library.")
        def get(self):
            return get_radio()

    @ns.route("/Library/Playlist/Get")
    class LibraryPlaylistGetResource(Resource):
        @ns.doc(summary="Get playlist items", description="Returns the available playlist entries and metadata.")
        def get(self):
            return get_playlist()

    @ns.route("/Podcast/Decode")
    class PodcastDecodeResource(Resource):
        @ns.doc(summary="Decode a podcast feed", description="Parses and decodes the requested podcast RSS feed or catalog metadata.")
        def get(self):
            return parse_podcast()

    @ns.route("/Library/Podcast/Get")
    class LibraryPodcastGetResource(Resource):
        @ns.doc(summary="Get podcast items", description="Returns the podcast items available in the library.")
        def get(self):
            return get_podcasts()

    @ns.route("/Library/Backup")
    class LibraryBackupResource(Resource):
        @ns.doc(summary="Backup the library", description="Creates a backup snapshot of the current library state.")
        def get(self):
            return Library_Backup()

    @ns.route("/Library/Restore")
    class LibraryRestoreResource(Resource):
        @ns.doc(summary="Restore the library", description="Restores the media library from the stored backup snapshot.")
        def get(self):
            return Library_Restore()

    @ns.route("/Library/SetTag")
    class LibrarySetTagResource(Resource):
        @ns.doc(summary="Set a tag on library objects", description="Sets a tag value on the selected library objects.")
        def get(self):
            return Set_Tag()

    @ns.route("/Library/GetValues")
    class LibraryGetValuesResource(Resource):
        @ns.doc(summary="Get all possible values for a set of tags", description="Returns all valid values available for the requested tag set.")
        def get(self):
            return GetAllValuesOfField()

    @ns.route("/Library/FindFiles")
    class LibraryFindFilesResource(Resource):
        @ns.doc(summary="Find files by query", description="Finds files matching the requested query or filter.")
        def get(self):
            return findfiles()

    @ns.route("/Library/Find")
    class LibraryFindResource(Resource):
        @ns.doc(summary="Find library entries by display query", description="Searches the library by display query and returns matching entries.")
        def get(self):
            return find()

    @ns.route("/Display/Covers")
    class DisplayCoversResource(Resource):
        @ns.doc(summary="Get cover display metadata", description="Builds the cover metadata used by the display layer.")
        def get(self):
            return Display_Covers()

    @ns.route("/Display/Group")
    class DisplayGroupResource(Resource):
        @ns.doc(summary="Build grouped display metadata", description="Builds the grouped display metadata used by the UI.")
        def get(self):
            return Display_Group()

    @ns.route("/Display/Files")
    class DisplayFilesResource(Resource):
        @ns.doc(summary="Build file displays", description="Creates the structured file metadata used for display rendering.")
        def get(self):
            return Display_Files()

    @ns.route("/SideFiles")
    class SideFilesResource(Resource):
        @ns.doc(summary="Get additional sidecar files", description="Returns supplementary sidecar files associated with the media library entries.")
        def get(self):
            return get_files_list()

    @ns.route("/SideFile/<dirhash>/<folder>/<filename>")
    class SideFileNestedResource(Resource):
        @ns.doc(summary="Serve a sidecar file from a nested folder", description="Serves a sidecar file stored in a nested folder for the given media hash.", params={"dirhash": "Directory hash identifier", "folder": "Folder path inside the sidecar tree", "filename": "Sidecar file name"})
        def get(self, dirhash, folder, filename):
            return get_file2(dirhash, folder, filename)

    @ns.route("/SideFile/<dirhash>/<filename>")
    class SideFileResource(Resource):
        @ns.doc(summary="Serve a sidecar file", description="Serves the requested sidecar file for the given media hash.", params={"dirhash": "Directory hash identifier", "filename": "Sidecar file name"})
        def get(self, dirhash, filename):
            return get_file(dirhash, filename)

    @ns.route("/Thumbnails/Epoch")
    class ThumbnailsEpochResource(Resource):
        @ns.doc(summary="Get thumbnail epoch ids", description="Returns the thumbnail epoch identifiers used for cache invalidation.")
        def get(self):
            return thumb_epoch()

    @ns.route("/Thumbnails/<dirhash>.jpg")
    class ThumbnailsResource(Resource):
        @ns.doc(summary="Serve a thumbnail image", description="Returns the thumbnail image associated with the given media hash.", params={"dirhash": "Thumbnail directory hash identifier"})
        def get(self, dirhash):
            return thumb(dirhash)

    @ns.route("/Covers/<dirhash>.jpg")
    class CoversResource(Resource):
        @ns.doc(summary="Serve a cover image", description="Returns the cover image associated with the given media hash.", params={"dirhash": "Cover directory hash identifier"})
        def get(self, dirhash):
            return cover(dirhash)

    @ns.route("/Web/Assets/<file>")
    class WebAssetsResource(Resource):
        @ns.doc(summary="Serve web asset files", description="Serves the requested static web asset from the application bundle.", params={"file": "Asset file path to serve"})
        def get(self, file):
            return get_assets(file)

    @ns.route("/Menu/Get")
    class MenuGetResource(Resource):
        @ns.doc(summary="Get the UI menu configuration", description="Returns the menu structure used by the frontend application.")
        def get(self):
            return menu()

    @ns.route("/Menu/Set")
    class MenuSetResource(Resource):
        @ns.doc(summary="Save menu configuration", description="Persists the menu configuration sent by the client UI.")
        def post(self):
            return save_menu()

    @ns.route("/Settings/Get")
    class SettingsGetResource(Resource):
        @ns.doc(summary="Get application settings", description="Returns the current application settings and configuration values.")
        def get(self):
            return Get_Settings()

    @ns.route("/Settings/Set")
    class SettingsSetResource(Resource):
        @ns.doc(summary="Set application settings", description="Updates the application settings with the values provided by the client.")
        def get(self):
            return Set_Settings()

    @ns.route("/Commands/Get")
    class CommandsGetResource(Resource):
        @ns.doc(summary="Get configured commands", description="Returns the list of configured system commands available to the application.")
        def get(self):
            return Commands_Get()

    @ns.route("/Commands/Run")
    class CommandsRunResource(Resource):
        @ns.doc(summary="Run a configured command", description="Executes the configured command for the requested player or application action.")
        def get(self):
            return Commands_Run()

    @ns.route("/Playlists/Get")
    class PlaylistsGetResource(Resource):
        @ns.doc(summary="Get playlists", description="Returns the playlists currently available to the client.")
        def get(self):
            return Playlists_Get()

    @ns.route("/UpdateCover")
    class UpdateCoverResource(Resource):
        @ns.doc(summary="Upload a cover image for a track", description="Uploads or updates a cover image associated with a track.")
        def post(self):
            return upload_file()

    @ns.route("/Upnp/Reload")
    class UpnpReloadResource(Resource):
        @ns.doc(summary="Reload UPnP configuration", description="Reloads the UPnP configuration and refreshes the available discovered devices.")
        def get(self):
            return Upnp_Reload()

    @ns.route("/Shutdown")
    class ShutdownResource(Resource):
        @ns.doc(summary="Shutdown the server", description="Stops the server cleanly and terminates the running service.")
        def get(self):
            return shutdown()

    @ns.route("/Goodbye")
    class GoodbyeResource(Resource):
        @ns.doc(summary="Goodbye endpoint", description="Graceful logout or goodbye endpoint used by the client session flow.")
        def get(self):
            return Goodbye()

    @ns.route("/Cache/ClearQueries")
    class ClearQueriesResource(Resource):
        @ns.doc(summary="Clear the saved query cache", description="Clears the saved query cache to force a fresh rebuild from source data.")
        def get(self):
            return ClearQueriesCache()

    @ns.route("/Login")
    class LoginResource(Resource):
        @ns.doc(summary="Log in to the API", description="Authenticates the user and returns the session token or login payload.")
        def get(self):
            return login()

    @ns.route("/Ports")
    class PortsResource(Resource):
        @ns.doc(summary="Get server ports", description="Returns the network ports exposed by the current server instance.")
        def get(self):
            return send_ip()

    @ns.route("/Stats")
    class StatsResource(Resource):
        @ns.doc(summary="Get library statistics", description="Returns statistics about the media library, tracks, and indexed content.")
        def get(self):
            return stats()

    @ns.route("/Rip/")
    class RipResource(Resource):
        @ns.doc(summary="Start the ripping workflow", description="Starts the CD ripping workflow and begins the import process.")
        def get(self):
            return ripcd()

    return ns
