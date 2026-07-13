import os
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, ContentSwitcher, TextArea, Markdown, DirectoryTree, Input, Button
from textual import on

class StandaloneMarkdownEditor(App):
    """A full-screen terminal Markdown Editor optimized for seamless navigation and text syntax injection."""
    CSS_PATH = "styles.tcss"

    def __init__(self):
        super().__init__()
        self.home_directory = Path.home()
        self.selected_directory = self.home_directory
        self.saved_selection_start = (0, 0)
        self.saved_selection_end = (0, 0)
        self.saved_selected_text = ""

    def compose(self) -> ComposeResult:
        with Horizontal(id="top-menu-bar"):
            yield Button("📁 Files", id="menu-files-btn", classes="menu-trigger-btn")
            yield Button("🎨 Styles", id="menu-styles-btn", classes="menu-trigger-btn")
            yield Button("❌ Quit", id="menu-quit-btn", classes="menu-trigger-btn")
            yield Button("🔄 Toggle Preview", id="btn-toggle-view")
        
        with Vertical(id="editor-workspace"):
            with ContentSwitcher(id="editor-switcher", initial="edit-view"):
                yield TextArea("# Standalone Document Editor\n\nClick the menu buttons at the top to configure files and styles!", id="edit-view")
                yield Markdown(id="preview-view")
                
                # --- INTERACTIVE EXPORT & IMPORT DIALOG VIEW ---
                with Horizontal(id="export-dialog-view"):
                    with Vertical(id="directory-picker-pane"):
                        yield Static("Select Directory or Open File:", id="picker-label")
                        yield DirectoryTree(self.home_directory, id="dir-tree")
                    
                    with Vertical(id="file-meta-pane"):
                        yield Static("Confirm Output Parameters:", id="meta-label")
                        yield Static(f"Target Directory: {self.selected_directory}", id="target-dir-display")
                        yield Static("[Tip: Double-click an existing file in the tree to open it directly!]", id="open-tip-display")
                        yield Input(placeholder="Enter custom filename here (e.g. document)", id="filename-input")
                        
                        with Horizontal(id="dialog-actions-row"):
                            yield Button("Save as Markdown (.md)", id="confirm_md", classes="dialog-btn save-action")
                            yield Button("Save as Plain Text (.txt)", id="confirm_txt", classes="dialog-btn save-action")
                            yield Button("Cancel and Go Back", id="cancel_files", classes="dialog-btn cancel-action")

                # --- STYLE SELECTOR PANEL OVERLAY ---
                with Vertical(id="style-selector-view"):
                    yield Static("Select Markdown Syntax Token to Inject:", id="style-title-label")
                    with Horizontal(id="style-buttons-grid"):
                        yield Button("Heading 1 (#)", id="h1", classes="style-menu-btn")
                        yield Button("Heading 2 (##)", id="h2", classes="style-menu-btn")
                        yield Button("Bold (**)", id="bold", classes="style-menu-btn")
                        yield Button("Italic (*)", id="italic", classes="style-menu-btn")
                        yield Button("Code Block (```)", id="code", classes="style-menu-btn")
                        yield Button("Bullet List (-)", id="list", classes="style-menu-btn")
                        yield Button("Hyperlink [🔗]", id="link", classes="style-menu-btn")
                        yield Button("Paragraph [📝]", id="paragraph", classes="style-menu-btn")
                    yield Button("Cancel and Return to Editor", id="cancel_styles", classes="style-back-btn")

                # --- INTERACTIVE HYPERLINK POPUP PANEL ---
                with Vertical(id="url-popup-view"):
                    yield Static("Enter or Paste Target Hyperlink Destination URL:", id="url-title-label")
                    yield Input(placeholder="https://example.com", id="url-input")
                    with Horizontal(id="url-actions-row"):
                        yield Button("Confirm and Inject Link", id="confirm_url_injection", classes="dialog-btn save-action")
                        yield Button("Cancel", id="cancel_url", classes="dialog-btn cancel-action")

                # --- DISCARD QUIT OVERLAY VIEW ---
                with Vertical(id="quit-dialog-view"):
                    yield Static("Are you sure you want to discard your changes and exit?", id="quit-title-label")
                    with Horizontal(id="quit-actions-row"):
                        yield Button("Yes, Quit Immediately", id="quit_force", classes="quit-btn emergency-action")
                        yield Button("No, Return to Editor", id="cancel_quit", classes="quit-btn safe-action")
    def _switch_to_pane(self, pane_id: str, focus_target_id: str = None) -> None:
        """Centralized method for handling smooth component panel switches."""
        self.query_one("#editor-switcher", ContentSwitcher).current = pane_id
        if focus_target_id:
            self.query_one(f"#{focus_target_id}").focus()

    @on(DirectoryTree.DirectorySelected)
    def handle_directory_selection(self, event: DirectoryTree.DirectorySelected) -> None:
        """Updates targeted file save paths cleanly when folder rows are clicked."""
        self.selected_directory = event.path
        self.query_one("#target-dir-display", Static).update(f"Target Directory: {self.selected_directory}")

    @on(DirectoryTree.FileSelected)
    def handle_file_opening(self, event: DirectoryTree.FileSelected) -> None:
        """Reads file payloads straight back into your text area editor."""
        file_path = event.path
        text_area = self.query_one("#edit-view", TextArea)
        
        if file_path.suffix.lower() in (".md", ".txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_contents = f.read()
                
                text_area.text = file_contents
                self.notify(f"Successfully loaded: {file_path.name}", title="File Opened")
                self._switch_to_pane("edit-view", "edit-view")
            except Exception as e:
                self.notify(f"Could not open file: {str(e)}", title="Load Failure", severity="error")
        else:
            self.notify("The editor can only ingest .md or .txt document templates!", title="Unsupported Format", severity="warning")

    @on(Markdown.LinkClicked)
    def handle_markdown_link_clicks(self, event: Markdown.LinkClicked) -> None:
        """CRASH FIX: Intercepts active links clicked inside the preview pane to prevent a terminal crash."""
        event.prevent_default()
        self.notify(f"Link clicked: {event.href}", title="Hyperlink Blocked")

    @on(Button.Pressed)
    def handle_button_actions(self, message: Button.Pressed) -> None:
        """Processes toolbar selections, structural formatting changes, and safe disk export writes."""
        button_id = message.button.id
        text_area = self.query_one("#edit-view", TextArea)
        markdown_viewer = self.query_one("#preview-view", Markdown)

        if button_id == "menu-files-btn":
            self.query_one("#dir-tree", DirectoryTree).reload()
            self._switch_to_pane("export-dialog-view", "filename-input")
            return
        elif button_id == "menu-styles-btn":
            self.saved_selection_start, self.saved_selection_end = text_area.selection
            self.saved_selected_text = text_area.selected_text
            self._switch_to_pane("style-selector-view")
            return
        elif button_id == "menu-quit-btn":
            self._switch_to_pane("quit-dialog-view")
            return

        if button_id == "btn-toggle-view":
            switcher = self.query_one("#editor-switcher", ContentSwitcher)
            if switcher.current == "edit-view":
                markdown_viewer.update(text_area.text)
                self._switch_to_pane("preview-view")
                markdown_viewer.refresh(layout=True)
            else:
                self._switch_to_pane("edit-view", "edit-view")
            return

        if button_id in ("cancel_files", "cancel_styles", "cancel_url", "cancel_quit"):
            self._switch_to_pane("edit-view", "edit-view")
            return

        if button_id == "quit_force":
            self.exit()
            return

        if button_id == "confirm_url_injection":
            url_input = self.query_one("#url-input", Input)
            destination_url = url_input.value.strip() or "url"
            label = self.saved_selected_text or "text"
            text_area.replace(f"[{label}]({destination_url})", self.saved_selection_start, self.saved_selection_end)
            url_input.value = ""
            self._switch_to_pane("edit-view", "edit-view")
            return

        if button_id in ("confirm_md", "confirm_txt"):
            filename_input = self.query_one("#filename-input", Input)
            filename = filename_input.value.strip()
            if not filename:
                self.notify("Please supply a valid filename string first!", title="Error", severity="error")
                filename_input.focus()
                return
            
            base_filename, _ = os.path.splitext(filename)
            extension = ".md" if button_id == "confirm_md" else ".txt"
            final_path = self.selected_directory / f"{base_filename}{extension}"
            
            try:
                with open(final_path, "w", encoding="utf-8") as f:
                    f.write(text_area.text)
                self.notify(f"File dumped safely to {final_path.name}!", title="Save Successful")
                self._switch_to_pane("edit-view", "edit-view")
            except Exception as e:
                self.notify(f"Could not write file: {str(e)}", title="Write Failure", severity="error")
            return
        start, end = self.saved_selection_start, self.saved_selection_end
        selected = self.saved_selected_text

        if button_id == "link":
            self._switch_to_pane("url-popup-view", "url-input")
            return

        style_buttons = ("bold", "italic", "code", "h1", "h2", "list", "paragraph")

        if button_id in style_buttons:
            # FIXED INLINE DISPATCHER: Isolate string definitions explicitly to stop Heading 2 crosstalk links
            if start != end:
                if button_id == "h1":
                    text_area.replace(f"# {selected}", start, end)
                elif button_id == "h2":
                    text_area.replace(f"## {selected}", start, end)
                elif button_id == "bold":
                    text_area.replace(f"**{selected}**", start, end)
                elif button_id == "italic":
                    text_area.replace(f"*{selected}*", start, end)
                elif button_id == "code":
                    text_area.replace(f"```\n{selected}\n```\n", start, end)
                elif button_id == "paragraph":
                    text_area.replace(f"\n\n{selected}\n\n", start, end)
                elif button_id == "list":
                    text_area.replace("\n".join(f"- {l}" if l.strip() else l for l in selected.split("\n")), start, end)
            else:
                if button_id == "h1":
                    text_area.replace("# ", start, end)
                elif button_id == "h2":
                    text_area.replace("## ", start, end)
                elif button_id == "bold":
                    text_area.replace("****", start, end)
                elif button_id == "italic":
                    text_area.replace("*italic*", start, end)  
                elif button_id == "code":
                    text_area.replace("```\n\n```\n", start, end)
                elif button_id == "paragraph":
                    text_area.replace("\n\n", start, end)
                elif button_id == "list":
                    text_area.replace("- ", start, end)

        self._switch_to_pane("edit-view", "edit-view")

if __name__ == "__main__":
    StandaloneMarkdownEditor().run()
