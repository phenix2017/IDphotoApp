#!/usr/bin/env python3
"""Streamlit GUI for IDphotoApp - Interactive photo processing interface."""

import streamlit as st
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import io

from background_engine import BACKGROUND_ENGINES, selected_background_engine
from crop_engine import (
    clamp_crop_rect,
    default_manual_crop_rect,
    manual_crop_metrics,
    manual_crop_suggestions,
)
from photo_service import (
    build_front_back_sheet_for_cards,
    build_print_sheet_for_photo,
    clean_id_card_photo,
    decode_image_bytes,
    encode_png_bytes,
)
from print_sheet import LayoutSpec, parse_layout
from process_photo import detect_face, crop_to_spec, get_foreground_alpha, replace_background
from spec_loader import load_photo_specs

try:
    from streamlit_image_coordinates import streamlit_image_coordinates
except ImportError:
    streamlit_image_coordinates = None


def _border_stats(image_bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    h, w = image_bgr.shape[:2]
    border = np.concatenate(
        [
            image_bgr[0:5, :, :].reshape(-1, 3),
            image_bgr[h - 5 : h, :, :].reshape(-1, 3),
            image_bgr[:, 0:5, :].reshape(-1, 3),
            image_bgr[:, w - 5 : w, :].reshape(-1, 3),
        ],
        axis=0,
    )
    mean = np.mean(border, axis=0)
    std = np.std(border, axis=0)
    return mean, std


def _max_copies_for_layout(
    photo_w: int,
    photo_h: int,
    layout: LayoutSpec,
    dpi: int,
    margin_in: float,
    spacing_in: float,
) -> int:
    sheet_w = int(round(layout.width_in * dpi))
    sheet_h = int(round(layout.height_in * dpi))
    margin = int(round(margin_in * dpi))
    spacing = int(round(spacing_in * dpi))

    available_width = sheet_w - 2 * margin
    available_height = sheet_h - 2 * margin
    if available_width <= 0 or available_height <= 0:
        return 0

    max_cols_orig = max(1, (available_width + spacing) // (photo_w + spacing))
    max_rows_orig = max(1, (available_height + spacing) // (photo_h + spacing))
    total_photos_orig = max_cols_orig * max_rows_orig

    # rotated
    photo_w_rot, photo_h_rot = photo_h, photo_w
    max_cols_rot = max(1, (available_width + spacing) // (photo_w_rot + spacing))
    max_rows_rot = max(1, (available_height + spacing) // (photo_h_rot + spacing))
    total_photos_rot = max_cols_rot * max_rows_rot

    return max(total_photos_orig, total_photos_rot)


def _draw_horizontal_guide(
    image: np.ndarray,
    x1: int,
    x2: int,
    y: int,
    label: str,
    color: tuple[int, int, int],
    tolerance_px: int = 0,
) -> None:
    if tolerance_px > 0:
        cv2.line(image, (x1, y - tolerance_px), (x2, y - tolerance_px), color, 1)
        cv2.line(image, (x1, y + tolerance_px), (x2, y + tolerance_px), color, 1)
    cv2.line(image, (x1, y), (x2, y), color, 2)
    cv2.putText(image, label, (x1 + 6, max(14, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)


@st.cache_data(show_spinner=False, max_entries=16)
def _cached_replace_background(
    image_png: bytes,
    background_rgb: tuple[int, int, int],
    face_bbox: tuple[int, int, int, int] | None,
    bg_tolerance: float,
    face_protect: float,
    engine: str,
) -> np.ndarray:
    data = np.frombuffer(image_png, dtype=np.uint8)
    image_bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)
    with selected_background_engine(engine):
        return replace_background(
            image_bgr,
            background_rgb,
            face_bbox=face_bbox,
            bbox_expand_x=0.2,
            bbox_expand_y=0.3,
            bg_tolerance=bg_tolerance,
            face_protect=face_protect,
        )


# Configure page
st.set_page_config(
    page_title="ID Photo & Card Studio",
    page_icon=":material/badge:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Design tokens: a high-contrast, low-decoration palette suited to an official-document
# tool (government/health/legal conventions) rather than a consumer marketing app.
#   --color-primary:   #0F172A (headers, borders, key text)
#   --color-secondary: #334155 (body/secondary text)
#   --color-accent:    #0369A1 (buttons, links, callouts — also .streamlit/config.toml primaryColor)
#   --color-muted:     #E8ECF1 (panel backgrounds)
#   --color-background:#F8FAFC (page background)
#   --color-border:    #E2E8F0
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600;700&family=Source+Sans+3:wght@400;500;600&display=swap');

    :root {
        --color-primary: #0F172A;
        --color-secondary: #334155;
        --color-accent: #0369A1;
        --color-muted: #E8ECF1;
        --color-background: #F8FAFC;
        --color-border: #E2E8F0;
    }

    html, body, [class*="css"] {
        font-family: 'Source Sans 3', 'Source Sans Pro', sans-serif;
    }

    /* Main container padding */
    .main {
        padding: 1rem;
        background-color: var(--color-background);
    }

    /* Header styling */
    h1 {
        font-family: 'Lexend', 'Source Sans 3', sans-serif;
        text-align: center;
        color: var(--color-primary);
        padding-bottom: 1rem;
        border-bottom: 3px solid var(--color-primary);
        margin-bottom: 1.5rem;
    }

    h2 {
        font-family: 'Lexend', 'Source Sans 3', sans-serif;
        color: var(--color-primary);
        padding-top: 0.5rem;
        border-left: 5px solid var(--color-primary);
        padding-left: 1rem;
        margin-top: 1.5rem;
    }

    h3 {
        font-family: 'Lexend', 'Source Sans 3', sans-serif;
        color: var(--color-secondary);
        margin-top: 1rem;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--color-muted);
        border-radius: 0.5rem;
    }

    /* Button styling */
    button {
        border-radius: 0.5rem;
        font-weight: 600;
    }

    /* Info/Warning boxes */
    .stInfo, .stWarning, .stSuccess {
        border-radius: 0.5rem;
        padding: 1rem;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }

    /* Metric styling */
    .metric {
        background-color: var(--color-muted);
        border-radius: 0.5rem;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("ID Photo & Card Studio")
st.markdown("""
<div style="text-align: center; color: var(--color-secondary); margin-bottom: 1rem;">
    <p><strong>Passport photos and ID cards, ready to print</strong></p>
    <p style="font-size: 0.9rem;">Auto-crop, background cleanup, and print-ready pages for passport/visa photos and ID cards</p>
</div>
""", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: var(--color-accent); background-color: var(--color-muted); border-radius: 0.5rem;
            padding: 0.6rem 1rem; margin-bottom: 1.5rem; font-size: 0.9rem;">
    Your photos are processed only for this session and are never uploaded to a third party or stored
    afterward &mdash; the only copy saved anywhere is the one you choose to download.
</div>
""", unsafe_allow_html=True)

# Load specs early
specs_path = Path(__file__).resolve().parent / "specs.json"
specs = load_photo_specs(specs_path)

# Placed at the very top of the sidebar (rather than the main content area) since it's the
# single control that governs every other setting below it.
with st.sidebar:
    st.markdown("### What are you creating?")
    document_type = st.radio(
        "What are you creating?",
        ["Passport / Visa photo", "ID card (front & back)"],
        index=0,
        label_visibility="collapsed",
        help="Passport/Visa: crop and format a headshot to an official photo spec. "
        "ID card: clean up front/back photos of an existing card and place both on one printable page.",
    )
    st.divider()

if document_type == "Passport / Visa photo":
    # Show profile requirements
    with st.expander("Profile Requirements & Visual Guide", expanded=False):
        col_req1, col_req2, col_req3 = st.columns(3)

        with col_req1:
            st.markdown("### Head to Shoulder Profile")
            st.markdown("""
            **Required Frame:**
            - **Top**: Top of head (minimal forehead)
            - **Bottom**: Mid-chest, shoulders visible
            - **Sides**: Both ears visible, face centered
            - **Eyes**: Horizontal center of frame

            **Head Position:**
            - Straight on, looking at camera
            - Head fills 50-70% of frame height
            - Neutral expression
            - Eyes open, mouth closed
            """)

        with col_req2:
            st.markdown("### Standards by Country (50+ Countries)")

            # Create tabs for better organization
            tab_major, tab_all = st.tabs(["Major Countries", "All Countries"])

            with tab_major:
                st.markdown("**Popular immigration destinations:**")
                major_codes = ["US_PASSPORT", "US_VISA", "CA_PASSPORT", "CA_VISA", "UK_PASSPORT", "UK_VISA", 
                              "AU_PASSPORT", "AU_VISA", "JP_PASSPORT", "JP_VISA", "SG_PASSPORT", "SG_VISA"]
                for code in major_codes:
                    if code in specs:
                        spec = specs[code]
                        w_in = spec.width_in if hasattr(spec, 'width_in') else spec.width_in
                        h_in = spec.height_in if hasattr(spec, 'height_in') else spec.height_in
                        st.write(f"**{spec.name}** • {w_in}\" × {h_in}\" | Head: {spec.head_height_ratio:.0%}")

            with tab_all:
                st.markdown(f"**All {len(specs)} specifications:**")
                cols_display = st.columns(2)
                for idx, (code, spec) in enumerate(specs.items()):
                    col = cols_display[idx % 2]
                    with col:
                        w_in = spec.width_in if hasattr(spec, 'width_in') else spec.width_in
                        h_in = spec.height_in if hasattr(spec, 'height_in') else spec.height_in
                        st.caption(f"{spec.name} • {w_in}\" × {h_in}\"")

        with col_req3:
            st.markdown("### Best Practices")
            st.markdown("""
            **Lighting:**
            - Even, bright lighting
            - No harsh shadows
            - Avoid backlighting

            **Background:**
            - Plain, uniform color
            - Preferably white or light gray
            - No patterns or people

            **Pose:**
            - Straight posture
            - Square shoulders
            - Face parallel to camera
            - Natural expression
            """)

        # Create visual example
        st.markdown("---")
        st.markdown("### Visual Examples")

        col_example1, col_example2 = st.columns(2)
        with col_example1:
            st.markdown("**GOOD PROFILE**")
            # Create simple visual guide
            example_img = np.ones((400, 300, 3), dtype=np.uint8) * 240
            # Head and shoulders outline
            cv2.rectangle(example_img, (50, 30), (250, 280), (50, 150, 50), 3)
            cv2.putText(example_img, "Top of head", (70, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
            cv2.putText(example_img, "Mid-chest", (80, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
            cv2.line(example_img, (150, 150), (150, 150), (100, 200, 100), 3)  # Eyes line
            st.image(Image.fromarray(example_img), use_container_width=True)

        with col_example2:
            st.markdown("**COMMON MISTAKES**")
            mistake_img = np.ones((400, 300, 3), dtype=np.uint8) * 240
            cv2.rectangle(mistake_img, (30, 80), (270, 350), (200, 50, 50), 3)
            cv2.putText(mistake_img, "Too much forehead", (50, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 50, 50), 1)
            cv2.putText(mistake_img, "Too much body", (80, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 50, 50), 1)
            st.image(Image.fromarray(mistake_img), use_container_width=True)

# Sidebar controls
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding-bottom: 1rem;">
        <h2 style="margin: 0; border: none; padding: 0;">⚙️ Settings</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if document_type == "Passport / Visa photo":
        # Country selection
        st.markdown("### Country")
        country = st.selectbox(
            "Select your country or document",
            options=list(specs.keys()),
            format_func=lambda x: specs[x].name,
            help="Choose the country specification and document type for your ID photo",
            label_visibility="collapsed"
        )

        photo_situation = st.radio(
            "Photo situation",
            ["Normal photo", "Shadow or messy background", "Need to adjust crop", "Background only (no crop)"],
            index=0,
            help="Choose the closest situation. Most users only need this setting. "
            "'Background only' removes the background but keeps the original photo size and framing "
            "instead of cropping it to a passport/visa size.",
        )

        # Beginner defaults. The detailed controls below are available in Advanced.
        replace_bg_default = True
        background_engine_default = "Best quality (slower)" if photo_situation == "Shadow or messy background" else "Fast (recommended)"
        bg_tolerance_default = 45 if photo_situation == "Shadow or messy background" else 35
        show_guides_default = photo_situation == "Need to adjust crop"
    else:
        country = None
        photo_situation = None
        # ID card mode always wants a clean background; keep the best-quality defaults.
        replace_bg_default = True
        background_engine_default = "Best quality (slower)"
        bg_tolerance_default = 35
        show_guides_default = False

    with st.expander("Advanced", expanded=False):
        st.markdown("### Photo")
        replace_bg = st.checkbox("Clean background", value=replace_bg_default, help="Remove the original background and fill with a solid color")
        background_engine = st.selectbox(
            "Background method",
            list(BACKGROUND_ENGINES),
            index=list(BACKGROUND_ENGINES).index(background_engine_default),
            help="Best quality is slower but cleaner. Fast works well for most photos. Basic needs no downloaded model.",
            disabled=not replace_bg,
        )
        default_bg_label = "Use spec default" if document_type == "Passport / Visa photo" else "White (default)"
        background_color_options = {
            default_bg_label: None,
            "White": (255, 255, 255),
            "Off-white": (245, 245, 245),
            "Light gray": (230, 230, 230),
            "Blue": (0, 120, 255),
            "Light blue": (200, 220, 255),
        }
        if document_type == "Passport / Visa photo":
            # Transparent output only applies to the single cropped photo, not the ID
            # card's print page, so it's only offered where it actually does something.
            background_color_options["Transparent (PNG)"] = "transparent"
        background_color_choice = st.selectbox(
            "Background color",
            options=list(background_color_options.keys()),
            index=0,
            help="Choose a common background color for the final photo",
            disabled=not replace_bg,
        )
        st.markdown("Background cleanup range")
        tol_col1, tol_col2 = st.columns(2)
        with tol_col1:
            tol_min = st.number_input("Min", min_value=1, max_value=100, value=5, step=1, disabled=not replace_bg)
        with tol_col2:
            tol_max = st.number_input("Max", min_value=1, max_value=100, value=60, step=1, disabled=not replace_bg)
        if tol_max <= tol_min:
            tol_max = tol_min + 1
        bg_tolerance = st.slider(
            "Background cleanup strength",
            min_value=int(tol_min),
            max_value=int(tol_max),
            value=int(min(max(bg_tolerance_default, tol_min), tol_max)),
            step=1,
            help="Higher values remove more background but may affect the subject edge.",
            disabled=not replace_bg,
        )
        face_protect = st.slider(
            "Protect face area",
            min_value=0.25,
            max_value=0.6,
            value=0.4,
            step=0.05,
            help="Higher values preserve more area around the face.",
            disabled=not replace_bg,
        )
        dpi = st.slider("Print quality (DPI)", min_value=100, max_value=600, value=300, step=50, help="300 DPI is standard for photo printing. Higher values create larger files.")
        enforce_target = st.checkbox("Enforce spec head size", value=True, help="Force final crop to match the specification's head height (uncheck to allow looser framing)")
        
    st.divider()
    
    with st.expander("Print and preview options", expanded=False):
        st.markdown("### Print layout")
        layout_preset = st.radio("Paper size", ["4x6", "6x6", "Custom"], help="Select your print paper size")
        
        if layout_preset == "Custom":
            col_custom1, col_custom2 = st.columns(2)
            with col_custom1:
                layout_w = st.number_input("Width (in)", value=4.0, min_value=1.0, step=0.5)
            with col_custom2:
                layout_h = st.number_input("Height (in)", value=6.0, min_value=1.0, step=0.5)
            layout = LayoutSpec(width_in=layout_w, height_in=layout_h)
        else:
            layout = parse_layout(layout_preset)
        
        copies = None  # auto-calculated based on layout, photo size, margin, spacing
        
        st.markdown("#### Spacing")
        col_margin, col_spacing = st.columns(2)
        with col_margin:
            st.markdown("Margin")
            margin = st.number_input("Margin", value=0.02, min_value=0.0, step=0.01, label_visibility="collapsed", help="Distance from paper edges to photos")
        with col_spacing:
            st.markdown("Gap")
            spacing = st.number_input("Spacing", value=0.02, min_value=0.0, step=0.01, label_visibility="collapsed", help="Gap between photos on the sheet")
    
        st.markdown("### Preview")
        if document_type == "Passport / Visa photo":
            show_guides = st.checkbox(
                "Show crop guide lines",
                value=show_guides_default,
                help="Show crop frames and guide lines on previews.",
            )
        else:
            show_guides = False
        show_sheet_guides = st.checkbox("Show very light print cut lines", value=True, help="Add nearly invisible cut lines, outlines, and corner marks on the print sheet")
        if document_type == "Passport / Visa photo":
            show_mask_debug = st.checkbox(
                "Show background mask preview",
                value=False,
                help="Preview the mask: white = kept, black = removed.",
            )
        else:
            show_mask_debug = False

if document_type == "Passport / Visa photo":
    # Main content area
    st.markdown("---")
    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        st.markdown("### Upload photo")
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=["jpg", "jpeg", "png"],
            help="Upload a clear, front-facing photo (JPG or PNG)",
            label_visibility="collapsed",
        )

    with col2:
        st.markdown("### File")
        if uploaded_file:
            st.success(f"Uploaded: **{uploaded_file.name}**")
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.info(f"Size: {file_size_mb:.2f} MB")
        else:
            st.info("Upload a photo to get started")

    # Process photo if uploaded
    if uploaded_file:
        upload_key = f"{uploaded_file.name}:{uploaded_file.size}"
        if st.session_state.get("last_upload_key") != upload_key:
            st.session_state.last_upload_key = upload_key
            st.session_state.create_requested = False

        if st.button("Create ID photo", type="primary", use_container_width=True):
            st.session_state.create_requested = True

        if not st.session_state.get("create_requested", False):
            st.stop()

        try:
            # Read the uploaded image. Use getvalue() rather than read(): Streamlit can
            # return the same UploadedFile across reruns, and read() would come back
            # empty/truncated once its position has already been consumed once.
            try:
                image_bgr = decode_image_bytes(uploaded_file.getvalue())
            except ValueError as exc:
                st.error(str(exc))
                image_bgr = None

            if image_bgr is not None:
                # The photo situation chooses the processing path automatically.
                if photo_situation == "Need to adjust crop":
                    processing_mode = "Manual Adjustment"
                elif photo_situation == "Background only (no crop)":
                    processing_mode = "Background Only"
                else:
                    processing_mode = "Automatic"
                background_only = processing_mode == "Background Only"

                with st.spinner("Processing..."):
                    transparent_bg = replace_bg and (background_color_choice == "Transparent (PNG)")
                    background_rgb = background_color_options.get(background_color_choice)
                    if background_rgb in (None, "transparent"):
                        background_rgb = specs[country].background_rgb
                    pad_rgb = background_rgb if replace_bg else specs[country].background_rgb

                    # Detect face
                    bbox, eye_point = detect_face(image_bgr)

                    if background_only:
                        # Keep the original framing and size; only the background is touched.
                        cropped_bgr = image_bgr.copy()
                    else:
                        # Crop to spec
                        cropped_bgr = crop_to_spec(
                            image_bgr,
                            bbox,
                            eye_point,
                            specs[country],
                            dpi,
                            background_rgb=pad_rgb,
                            enforce_target=bool(enforce_target),
                        )

                    # Replace after cropping so the cutout edge is generated at final resolution.
                    if replace_bg and not transparent_bg:
                        try:
                            bbox_cropped, _ = detect_face(cropped_bgr)
                        except Exception:
                            bbox_cropped = None
                        cropped_bgr = _cached_replace_background(
                            encode_png_bytes(cropped_bgr),
                            tuple(background_rgb),
                            tuple(int(v) for v in bbox_cropped) if bbox_cropped is not None else None,
                            float(bg_tolerance),
                            float(face_protect),
                            background_engine,
                        )

                    # Optional debug mask preview
                    if replace_bg and show_mask_debug:
                        with st.expander("Background Mask Preview", expanded=True):
                            dbg_col1, dbg_col2 = st.columns(2)
                            with dbg_col1:
                                try:
                                    with selected_background_engine(background_engine):
                                        mask_orig = get_foreground_alpha(
                                            image_bgr,
                                            face_bbox=bbox,
                                            bbox_expand_x=0.4,
                                            bbox_expand_y=0.6,
                                            bg_tolerance=float(bg_tolerance),
                                            face_protect=float(face_protect),
                                        )
                                    fg_ratio = float(np.mean(mask_orig > 0))
                                    mean, std = _border_stats(image_bgr)
                                    st.caption(f"Original mask fg: {fg_ratio:.2f} | border mean: {mean.astype(int)} | border std: {std.astype(int)} | white=kept")
                                    st.image(Image.fromarray(mask_orig), caption="Original mask", use_container_width=True)
                                except Exception as exc:
                                    st.error(f"Mask debug failed (original): {exc}")
                            with dbg_col2:
                                try:
                                    bbox_dbg, _ = detect_face(cropped_bgr)
                                except Exception:
                                    bbox_dbg = None
                                try:
                                    with selected_background_engine(background_engine):
                                        mask_crop = get_foreground_alpha(
                                            cropped_bgr,
                                            face_bbox=bbox_dbg,
                                            bbox_expand_x=0.2,
                                            bbox_expand_y=0.3,
                                            bg_tolerance=float(bg_tolerance),
                                            face_protect=float(face_protect),
                                        )
                                    fg_ratio = float(np.mean(mask_crop > 0))
                                    mean, std = _border_stats(cropped_bgr)
                                    st.caption(f"Cropped mask fg: {fg_ratio:.2f} | border mean: {mean.astype(int)} | border std: {std.astype(int)} | white=kept")
                                    st.image(Image.fromarray(mask_crop), caption="Cropped mask", use_container_width=True)
                                except Exception as exc:
                                    st.error(f"Mask debug failed (cropped): {exc}")

                    # Convert to RGB for display
                    cropped_rgb = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
                    cropped_pil = Image.fromarray(cropped_rgb)

                # Manual adjustment mode
                if processing_mode == "Manual Adjustment":
                    st.markdown("---")
                    st.markdown("""
                    <div style="background-color: var(--color-muted); border-left: 5px solid var(--color-primary); padding: 1.25rem 1.5rem; border-radius: 0.5rem;">
                        <h2 style="color: var(--color-primary); border: none; margin-top: 0;">Manual Crop Adjustment</h2>
                        <p style="color: var(--color-secondary); margin: 0;">Head &amp; shoulder profile framing</p>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("""
                    **Your goal**: position the crop frame to capture head and shoulders correctly.
                    Use the controls below to fine-tune the crop area.
                    """)

                    # Show visual guide and instructions
                    tab1, tab2 = st.tabs(["Instructions", "Visual Guide"])

                    with tab1:
                        col_instr1, col_instr2 = st.columns(2)
                        with col_instr1:
                            st.markdown("### Correct Framing")
                            st.markdown("""
                            **Head Position:**
                            - Top: Include full head, minimal forehead
                            - Leave ~10-15% space above head
                            - Eyes roughly in middle of frame

                            **Shoulder Position:**
                            - Bottom: Include shoulders and mid-chest
                            - Show natural shoulder width
                            - Keep chest down to mid-torso
                            """)

                        with col_instr2:
                            st.markdown("### Common Mistakes")
                            st.markdown("""
                            **To avoid:**
                            - Cutting off top of head
                            - Too much forehead
                            - Tilted head
                            - Shoulders cut off
                            - Too much upper body
                            - Uneven side framing
                            """)

                    with tab2:
                        col_img1, col_img2 = st.columns(2)
                        with col_img1:
                            st.markdown("**Good Profile Example:**")
                            good_guide = np.ones((300, 200, 3), dtype=np.uint8) * 240
                            # Draw head area
                            cv2.ellipse(good_guide, (100, 80), (40, 45), 0, 0, 360, (100, 100, 100), 2)
                            # Draw shoulders
                            cv2.line(good_guide, (60, 120), (140, 120), (100, 100, 100), 3)
                            # Draw frame
                            cv2.rectangle(good_guide, (40, 30), (160, 260), (0, 200, 0), 3)
                            # Labels
                            cv2.putText(good_guide, "Top", (70, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 150, 0), 1)
                            cv2.putText(good_guide, "Eyes", (95, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 150, 0), 1)
                            cv2.putText(good_guide, "Shoulders", (55, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 150, 0), 1)
                            cv2.putText(good_guide, "Bottom", (70, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 150, 0), 1)
                            st.image(Image.fromarray(good_guide), use_container_width=True)

                        with col_img2:
                            st.markdown("**Common Issues:**")
                            bad_guide = np.ones((300, 200, 3), dtype=np.uint8) * 240
                            # Too much forehead
                            cv2.rectangle(bad_guide, (40, 10), (160, 200), (200, 50, 50), 2)
                            cv2.putText(bad_guide, "Bad: Too much", (50, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 50, 50), 1)
                            cv2.putText(bad_guide, "forehead", (65, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 50, 50), 1)
                            # Cut off head
                            cv2.rectangle(bad_guide, (40, 60), (160, 280), (200, 150, 50), 2)
                            cv2.putText(bad_guide, "Bad: Head cut", (45, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 150, 50), 1)
                            st.image(Image.fromarray(bad_guide), use_container_width=True)

                    st.markdown("---")

                    # Slider controls for manual adjustment
                    st.markdown("### Manual Crop Controls")
                    st.markdown(
                        "*Use the controls on the left to resize and move the crop frame — "
                        "the preview on the right updates immediately.*"
                    )

                    # Get target photo specifications
                    spec = specs[country]

                    # Use original image without zoom
                    image_zoomed = image_bgr.copy()
                    h_zoom, w_zoom = image_zoomed.shape[:2]

                    # Controls sit directly beside the preview they affect (not above it), so
                    # adjusting and seeing the result don't require scrolling back and forth.
                    ctrl_col, preview_col1, preview_col2 = st.columns([1.2, 2, 2], gap="medium")

                    with ctrl_col:
                        st.markdown("#### Crop Size")
                        size_btn_col1, size_btn_col2 = st.columns(2, gap="small")
                        with size_btn_col1:
                            if st.button("Shrink", key="shrink_crop", icon=":material/remove:", help="Shrink crop area by 15%", use_container_width=True):
                                st.session_state.scale_factor = getattr(st.session_state, 'scale_factor', 1.0) - 0.15
                        with size_btn_col2:
                            if st.button("Enlarge", key="enlarge_crop", icon=":material/add:", help="Enlarge crop area by 15%", use_container_width=True):
                                st.session_state.scale_factor = getattr(st.session_state, 'scale_factor', 1.0) + 0.15

                        scale_display = getattr(st.session_state, 'scale_factor', 1.0)
                        st.metric("Scale Factor", f"{scale_display:.0%}", delta=None)

                        if st.button("Reset size", key="reset_crop", icon=":material/restart_alt:", use_container_width=True, help="Reset to default size"):
                            st.session_state.scale_factor = 1.0

                        st.markdown("#### Crop Position")

                        # Up button
                        if st.button("Up", key="move_up", icon=":material/arrow_upward:", use_container_width=True, help="Move up by 2%"):
                            st.session_state.move_offset_y = getattr(st.session_state, 'move_offset_y', 0) - 2

                        # Left/Right row
                        dir_col1, dir_col2 = st.columns(2, gap="small")
                        with dir_col1:
                            if st.button("Left", key="move_left", icon=":material/arrow_back:", use_container_width=True, help="Move left by 2%"):
                                st.session_state.move_offset_x = getattr(st.session_state, 'move_offset_x', 0) - 2
                        with dir_col2:
                            if st.button("Right", key="move_right", icon=":material/arrow_forward:", use_container_width=True, help="Move right by 2%"):
                                st.session_state.move_offset_x = getattr(st.session_state, 'move_offset_x', 0) + 2

                        # Down button
                        if st.button("Down", key="move_down", icon=":material/arrow_downward:", use_container_width=True, help="Move down by 2%"):
                            st.session_state.move_offset_y = getattr(st.session_state, 'move_offset_y', 0) + 2

                        move_x = getattr(st.session_state, 'move_offset_x', 0)
                        move_y = getattr(st.session_state, 'move_offset_y', 0)
                        st.metric("Position", f"({move_x:+d}%, {move_y:+d}%)", delta=None)

                        if st.button("Reset position", key="reset_pos", icon=":material/restart_alt:", use_container_width=True, help="Reset to center"):
                            st.session_state.move_offset_x = 0
                            st.session_state.move_offset_y = 0

                    # Apply scale factor from +/- buttons
                    scale_factor = getattr(st.session_state, 'scale_factor', 1.0)
                    scale_factor = max(0.5, min(2.0, scale_factor))  # Clamp between 0.5x and 2.0x

                    # Get movement offsets from directional buttons
                    move_offset_x = getattr(st.session_state, 'move_offset_x', 0)
                    move_offset_y = getattr(st.session_state, 'move_offset_y', 0)

                    # Start manual adjustment from the detected face/eyes and selected spec.
                    spec = specs[country]
                    base_x1, base_y1, base_x2, base_y2 = default_manual_crop_rect(
                        image_zoomed.shape,
                        bbox,
                        eye_point,
                        spec,
                    )
                    base_w = max(1, base_x2 - base_x1)
                    base_h = max(1, base_y2 - base_y1)
                    target_aspect = spec.width_in / spec.height_in
                    center_x = (base_x1 + base_x2) / 2 + (move_offset_x / 100) * w_zoom
                    center_y = (base_y1 + base_y2) / 2 + (move_offset_y / 100) * h_zoom

                    scaled_h = base_h * scale_factor
                    scaled_w = scaled_h * target_aspect
                    if scaled_w > w_zoom:
                        scaled_w = float(w_zoom)
                        scaled_h = scaled_w / target_aspect
                    if scaled_h > h_zoom:
                        scaled_h = float(h_zoom)
                        scaled_w = scaled_h * target_aspect

                    x1, y1, x2, y2 = clamp_crop_rect(
                        center_x - scaled_w / 2,
                        center_y - scaled_h / 2,
                        scaled_w,
                        scaled_h,
                        w_zoom,
                        h_zoom,
                    )

                    manual_cropped_bgr = image_zoomed[y1:y2, x1:x2]

                    # Resize to spec dimensions while minimizing aspect ratio distortion
                    w_px, h_px = int(round(spec.width_in * dpi)), int(round(spec.height_in * dpi))
                    target_aspect = w_px / h_px

                    # Get the aspect ratio of the manual crop
                    crop_h = y2 - y1
                    crop_w = x2 - x1
                    current_aspect = crop_w / crop_h

                    # Only resize if aspect ratio differs significantly (avoid unnecessary distortion)
                    if abs(current_aspect - target_aspect) < 0.1:
                        # Aspect ratios are similar - safe to resize
                        interpolation = cv2.INTER_AREA if (crop_w * crop_h > w_px * h_px) else cv2.INTER_CUBIC
                        manual_cropped_bgr = cv2.resize(manual_cropped_bgr, (w_px, h_px), interpolation=interpolation)
                    else:
                        # Aspect ratios differ - fit into target with padding to avoid face distortion
                        # Calculate how much space is available
                        scale_w = w_px / crop_w
                        scale_h = h_px / crop_h
                        scale = min(scale_w, scale_h)  # Use smaller scale to fit without distortion

                        # Resize maintaining aspect ratio
                        new_w = int(round(crop_w * scale))
                        new_h = int(round(crop_h * scale))
                        interpolation = cv2.INTER_AREA if (crop_w * crop_h > new_w * new_h) else cv2.INTER_CUBIC
                        manual_cropped_bgr = cv2.resize(manual_cropped_bgr, (new_w, new_h), interpolation=interpolation)

                        # Center in the target dimensions with background padding
                        result = np.full((h_px, w_px, 3), pad_rgb[::-1], dtype=np.uint8)
                        y_offset = (h_px - new_h) // 2
                        x_offset = (w_px - new_w) // 2
                        result[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = manual_cropped_bgr
                        manual_cropped_bgr = result

                    manual_cropped_rgb = cv2.cvtColor(manual_cropped_bgr, cv2.COLOR_BGR2RGB)
                    cropped_pil = Image.fromarray(manual_cropped_rgb)

                    # Update cropped_bgr to use manual adjustment
                    cropped_bgr = manual_cropped_bgr

                    # If user requested background cleanup, re-run background replacement
                    # on the manual-cropped image so the final result reflects the selection.
                    if replace_bg and not transparent_bg:
                        try:
                            bbox_cropped, _ = detect_face(cropped_bgr)
                        except Exception:
                            bbox_cropped = None
                        try:
                            cropped_bgr = _cached_replace_background(
                                encode_png_bytes(cropped_bgr),
                                tuple(background_rgb),
                                tuple(int(v) for v in bbox_cropped) if bbox_cropped is not None else None,
                                float(bg_tolerance),
                                float(face_protect),
                                background_engine,
                            )
                        except Exception:
                            # If background replacement fails here, keep the manual crop as-is
                            pass

                    # Validate estimated feature positioning against spec-driven targets.
                    crop_h = max(1, y2 - y1)
                    crop_w = max(1, x2 - x1)
                    metrics = manual_crop_metrics((x1, y1, x2, y2), bbox, eye_point, spec)
                    suggestions = manual_crop_suggestions(metrics)

                    # These tolerances account for face-detector variance while keeping the guides meaningful.
                    head_top_valid = abs(metrics["actual_head_top_ratio"] - metrics["target_head_top_ratio"]) <= 0.06
                    eye_valid = abs(metrics["actual_eye_ratio"] - metrics["target_eye_ratio"]) <= 0.05
                    head_size_valid = abs(metrics["actual_head_height_ratio"] - metrics["target_head_height_ratio"]) <= 0.10
                    center_aligned = metrics["actual_center_offset_ratio"] <= 0.08

                    # Overall validation
                    features_valid = all([head_top_valid, eye_valid, head_size_valid, center_aligned])

                    # Show live preview (optional overlay), directly beside the controls above.
                    with preview_col1:
                        st.markdown("#### Live Preview")
                        if show_guides:
                            st.markdown("*Green box shows the area that will be cropped. Guide lines help position key features correctly.*")
                            # Draw rectangle showing crop area on zoomed image
                            img_display = image_zoomed.copy()

                            # Draw outer rectangle with a thinner border
                            cv2.rectangle(img_display, (x1, y1), (x2, y2), (0, 200, 0), 2)

                            # Add guide lines for correct positioning
                            crop_h = y2 - y1
                            crop_w = x2 - x1
                            tolerance_px = max(2, int(crop_h * 0.025))

                            # Top of head guide
                            head_top_y = y1 + int(crop_h * spec.top_margin_ratio)
                            _draw_horizontal_guide(img_display, x1, x2, head_top_y, "Head top", (60, 170, 60), tolerance_px)

                            # Eye line tolerance zone
                            eye_line_y = y1 + int(crop_h * (1 - specs[country].eye_line_from_bottom_ratio))
                            _draw_horizontal_guide(img_display, x1, x2, eye_line_y, "Eyes", (200, 120, 40), tolerance_px)

                            # Head-size guide
                            head_bottom_y = y1 + int(crop_h * min(0.95, spec.top_margin_ratio + spec.head_height_ratio))
                            _draw_horizontal_guide(img_display, x1, x2, head_bottom_y, "Chin / head bottom", (120, 120, 220), tolerance_px)

                            # Add center vertical line
                            center_x_line = (x1 + x2) // 2
                            cv2.line(img_display, (center_x_line, y1), (center_x_line, y2), (200, 200, 200), 1)
                            cv2.putText(img_display, "Center", (center_x_line + 5, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (190, 190, 190), 1)

                            # Add corner markers
                            corner_size = 20
                            cv2.line(img_display, (x1, y1), (x1 + corner_size, y1), (0, 200, 255), 3)
                            cv2.line(img_display, (x1, y1), (x1, y1 + corner_size), (0, 200, 255), 3)

                            img_display_rgb = cv2.cvtColor(img_display, cv2.COLOR_BGR2RGB)
                            st.image(Image.fromarray(img_display_rgb), 
                                    caption=f"Original Image - Crop with Position Guides",
                                    use_container_width=True)
                        else:
                            img_display_rgb = cv2.cvtColor(image_zoomed, cv2.COLOR_BGR2RGB)
                            st.image(Image.fromarray(img_display_rgb), 
                                    caption="Original Image",
                                    use_container_width=True)

                        # Show crop dimensions below image
                        st.caption(f"Crop: {crop_w}×{crop_h} px | Scale: {scale_factor:.0%} | Pos: ({move_offset_x:+d}%, {move_offset_y:+d}%)")

                        # Show feature validation status
                        st.markdown("#### Feature Position Validation")
                        val_col1, val_col2, val_col3 = st.columns(3)
                        with val_col1:
                            if head_top_valid:
                                st.success("Head top", icon=":material/check_circle:")
                            else:
                                st.warning("Head top", icon=":material/warning:")
                        with val_col2:
                            if eye_valid:
                                st.success("Eyes", icon=":material/check_circle:")
                            else:
                                st.warning("Eyes", icon=":material/warning:")
                        with val_col3:
                            if head_size_valid:
                                st.success("Head size", icon=":material/check_circle:")
                            else:
                                st.warning("Head size", icon=":material/warning:")

                        val_col4, _ = st.columns(2)
                        with val_col4:
                            if center_aligned:
                                st.success("Centered", icon=":material/check_circle:")
                            else:
                                st.warning("Centered", icon=":material/warning:")

                        # Overall validation status
                        if features_valid:
                            st.success("All features in correct position — ready to save.", icon=":material/check_circle:")
                        else:
                            st.info("Adjust the crop frame to position all features correctly.", icon=":material/info:")
                        st.markdown("#### Recommended adjustment")
                        for suggestion in suggestions:
                            st.write(f"- {suggestion}")

                    with preview_col2:
                        st.markdown("#### Final Result")
                        # Display final photo (optional guide overlay)
                        final_photo_display = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
                        if show_guides:
                            # Add guide lines to final photo as well (Head Top / Eyes / Shoulders)
                            final_display = final_photo_display.copy()
                            final_h, final_w = final_display.shape[:2]
                            tolerance_px_final = max(2, int(final_h * 0.025))

                            # Top of head guide
                            head_top_final = int(final_h * spec.top_margin_ratio)
                            _draw_horizontal_guide(final_display, 0, final_w, head_top_final, "Head top", (60, 170, 60), tolerance_px_final)

                            # Eye line tolerance zone
                            eye_line_final = int(final_h * (1 - specs[country].eye_line_from_bottom_ratio))
                            _draw_horizontal_guide(final_display, 0, final_w, eye_line_final, "Eyes", (200, 120, 40), tolerance_px_final)

                            # Head-size guide
                            head_bottom_final = int(final_h * min(0.95, spec.top_margin_ratio + spec.head_height_ratio))
                            _draw_horizontal_guide(final_display, 0, final_w, head_bottom_final, "Chin / head bottom", (120, 120, 220), tolerance_px_final)

                            st.image(Image.fromarray(final_display), 
                                    caption="Final ID Photo with Guides",
                                    use_container_width=True)
                        else:
                            st.image(Image.fromarray(final_photo_display), 
                                    caption="Final ID Photo",
                                    use_container_width=True)
                    st.caption(f"{w_px:,} x {h_px:,} px | {specs[country].width_in}\" x {specs[country].height_in}\" @ {dpi} DPI")

                # Generate print sheet (for both automatic and manual modes; skipped for background-only
                # output since that isn't a fixed passport/visa size to tile).
                sheet = None
                effective_copies = 0
                if not background_only:
                    sheet_photo = cropped_pil.convert("RGB")
                    max_copies = _max_copies_for_layout(
                        photo_w=sheet_photo.size[0],
                        photo_h=sheet_photo.size[1],
                        layout=layout,
                        dpi=dpi,
                        margin_in=margin,
                        spacing_in=spacing,
                    )
                    effective_copies = max_copies
                    st.info(f"Copies per sheet (auto): {effective_copies}")
                    sheet = build_print_sheet_for_photo(
                        photo=sheet_photo,
                        layout=layout,
                        dpi=dpi,
                        margin_in=margin,
                        spacing_in=spacing,
                        copies=effective_copies,
                        draw_guides=show_sheet_guides,
                    )

                # Display results
                st.success("Photo processed successfully.")

                if background_only:
                    col_photo = st.container()
                    col_sheet = None
                else:
                    col_photo, col_sheet = st.columns(2)

                with col_photo:
                    st.subheader("Photo (background only)" if background_only else "Cropped Photo")
                    spec = specs[country]
                    w_in, h_in = spec.width_in, spec.height_in

                    # If transparent background requested, build RGBA output for display/download
                    if transparent_bg:
                        try:
                            bbox_cropped, _ = detect_face(cropped_bgr)
                        except Exception:
                            bbox_cropped = None
                        with selected_background_engine(background_engine):
                            fg_mask = get_foreground_alpha(
                                cropped_bgr,
                                face_bbox=bbox_cropped,
                                bbox_expand_x=0.2,
                                bbox_expand_y=0.3,
                                prefer_white_key=False,
                                bg_tolerance=float(bg_tolerance),
                                face_protect=float(face_protect),
                            )
                        rgba = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGBA)
                        rgba[:, :, 3] = fg_mask
                        cropped_pil = Image.fromarray(rgba)

                    # Display cropped photo without text overlay
                    if transparent_bg:
                        caption = "Background removed (transparent)" if background_only else f"{w_in}\" x {h_in}\" (transparent)"
                        st.image(cropped_pil, caption=caption, use_container_width=True)
                    else:
                        cropped_display = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
                        caption = "Background removed" if background_only else f"{w_in}\" x {h_in}\""
                        st.image(Image.fromarray(cropped_display), caption=caption, use_container_width=True)

                    # Photo size info
                    w_px, h_px = cropped_pil.size
                    if background_only:
                        st.caption(f"Size: {w_px:,} x {h_px:,} px (original framing kept, background only)")
                    else:
                        st.caption(f"Size: {w_px:,} x {h_px:,} px @ {dpi} DPI | {country} standard")

                    # Download cropped photo
                    img_buffer = io.BytesIO()
                    cropped_pil.save(img_buffer, format="PNG")
                    download_name = f"{country.lower()}_photo.png"
                    download_mime = "image/png"
                    img_buffer.seek(0)

                    st.download_button(
                        label="Download photo",
                        data=img_buffer,
                        file_name=download_name,
                        mime=download_mime,
                        use_container_width=True
                    )

                if col_sheet is not None:
                    with col_sheet:
                        st.subheader("Print Sheet")

                        # Display print sheet without text overlay
                        sheet_display = cv2.cvtColor(np.array(sheet), cv2.COLOR_RGB2BGR)
                        sheet_display_rgb = cv2.cvtColor(sheet_display, cv2.COLOR_BGR2RGB)
                        st.image(Image.fromarray(sheet_display_rgb), caption=f"Print layout: {layout.width_in}\" x {layout.height_in}\"", use_container_width=True)

                        # Sheet size info
                        sheet_w, sheet_h = sheet.size
                        st.caption(f"Sheet: {sheet_w:,} x {sheet_h:,} px @ {dpi} DPI | {effective_copies} copies")

                        # Download print sheet
                        sheet_buffer = io.BytesIO()
                        sheet.save(sheet_buffer, format="JPEG", quality=95)
                        sheet_buffer.seek(0)

                        st.download_button(
                            label="Download sheet",
                            data=sheet_buffer,
                            file_name=f"{country.lower()}_sheet_{int(layout.width_in)}x{int(layout.height_in)}.jpg",
                            mime="image/jpeg",
                            use_container_width=True
                        )

                with st.expander("Photo standard details", expanded=False):
                    col_specs1, col_specs2, col_specs3 = st.columns(3)
                    with col_specs1:
                        st.metric("Country", f"{country} - {specs[country].name}")
                    with col_specs2:
                        st.metric("Photo Size", f"{specs[country].width_in}\" x {specs[country].height_in}\"")
                    with col_specs3:
                        # Compute actual head fill for the produced photo (use face bbox or alpha mask)
                        actual_fill = None
                        try:
                            bbox_cropped, _ = detect_face(cropped_bgr)
                            bx, by, bw, bh = bbox_cropped
                            est_top = int(round(by - bh * 0.15))
                            est_bottom = int(round(by + bh))
                            head_h = max(1, est_bottom - est_top)
                            final_h = max(1, cropped_bgr.shape[0])
                            actual_fill = head_h / final_h
                        except Exception:
                            try:
                                with selected_background_engine(background_engine):
                                    mask_crop = get_foreground_alpha(
                                        cropped_bgr,
                                        face_bbox=None,
                                        bbox_expand_x=0.2,
                                        bbox_expand_y=0.3,
                                        bg_tolerance=float(bg_tolerance),
                                        face_protect=float(face_protect),
                                    )
                                ys, xs = np.where(mask_crop > 40)
                                if ys.size > 0:
                                    head_h = max(1, int(ys.max() - ys.min()))
                                    final_h = max(1, cropped_bgr.shape[0])
                                    actual_fill = head_h / final_h
                            except Exception:
                                actual_fill = None

                        if actual_fill is not None:
                            st.metric("Head Frame Coverage", f"{actual_fill:.0%}", delta=f"target {specs[country].head_height_ratio:.0%}")
                        else:
                            st.metric("Head Frame Coverage", f"{specs[country].head_height_ratio:.0%}")

        except RuntimeError as e:
            st.error(f"Error: {str(e)}")
            st.info("Try a clear front-facing photo with good lighting.")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            st.info("Please check that your image is valid and properly formatted.")

else:
    st.markdown("### Upload ID card front & back")
    card_col1, card_col2 = st.columns(2, gap="large")
    with card_col1:
        front_file = st.file_uploader(
            "Front of card",
            type=["jpg", "jpeg", "png"],
            help="Photo or scan of the front of the ID card",
        )
    with card_col2:
        back_file = st.file_uploader(
            "Back of card",
            type=["jpg", "jpeg", "png"],
            help="Photo or scan of the back of the ID card",
        )

    if not front_file or not back_file:
        st.info("Upload both the front and back of the card to continue.")
        st.stop()

    card_upload_key = f"{front_file.name}:{front_file.size}:{back_file.name}:{back_file.size}"
    if st.session_state.get("last_card_upload_key") != card_upload_key:
        st.session_state.last_card_upload_key = card_upload_key
        st.session_state.card_create_requested = False

    if st.button("Create ID card page", type="primary", use_container_width=True):
        st.session_state.card_create_requested = True

    if not st.session_state.get("card_create_requested", False):
        st.stop()

    try:
        try:
            front_bytes = front_file.getvalue()
            front_bgr = decode_image_bytes(front_bytes)
        except ValueError as exc:
            st.error(f"**Front of card** — {exc}")
            st.caption(f"File: {front_file.name} ({front_file.size:,} bytes)")
            st.stop()
        try:
            back_bytes = back_file.getvalue()
            back_bgr = decode_image_bytes(back_bytes)
        except ValueError as exc:
            st.error(f"**Back of card** — {exc}")
            st.caption(f"File: {back_file.name} ({back_file.size:,} bytes)")
            st.stop()

        with st.spinner("Cleaning up front & back..."):
            card_background_rgb = background_color_options.get(background_color_choice)
            if not isinstance(card_background_rgb, tuple):
                card_background_rgb = (255, 255, 255)

            if replace_bg:
                front_clean_bgr = clean_id_card_photo(
                    front_bgr, card_background_rgb, background_engine, float(bg_tolerance)
                )
                back_clean_bgr = clean_id_card_photo(
                    back_bgr, card_background_rgb, background_engine, float(bg_tolerance)
                )
            else:
                front_clean_bgr = front_bgr
                back_clean_bgr = back_bgr

        front_pil = Image.fromarray(cv2.cvtColor(front_clean_bgr, cv2.COLOR_BGR2RGB))
        back_pil = Image.fromarray(cv2.cvtColor(back_clean_bgr, cv2.COLOR_BGR2RGB))

        sheet = build_front_back_sheet_for_cards(
            front_pil,
            back_pil,
            layout=layout,
            dpi=dpi,
            margin_in=margin,
            spacing_in=spacing,
            draw_guides=show_sheet_guides,
        )

        st.success("Card page created.")

        col_front, col_back = st.columns(2)
        with col_front:
            st.subheader("Front (cleaned)")
            st.image(front_pil, use_container_width=True)
        with col_back:
            st.subheader("Back (cleaned)")
            st.image(back_pil, use_container_width=True)

        st.subheader("Print page")
        st.image(
            sheet,
            caption=f"Print layout: {layout.width_in}\" x {layout.height_in}\" | one front + one back, centered",
            use_container_width=True,
        )
        sheet_w, sheet_h = sheet.size
        st.caption(f"Sheet: {sheet_w:,} x {sheet_h:,} px @ {dpi} DPI")

        sheet_buffer = io.BytesIO()
        sheet.save(sheet_buffer, format="JPEG", quality=95)
        sheet_buffer.seek(0)
        st.download_button(
            label="Download page",
            data=sheet_buffer,
            file_name="id_card_front_back.jpg",
            mime="image/jpeg",
            use_container_width=True,
        )
    except RuntimeError as e:
        st.error(f"Error: {str(e)}")
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        st.info("Please check that your images are valid and properly formatted.")

# Instructions sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("How to use")
    with st.expander("Setup", expanded=False):
        st.markdown("""
        **Passport / Visa photo:**
        1. Select your country.
        2. Choose the photo situation.
        3. Upload a photo.
        4. Download the photo or print sheet.

        **ID card (front & back):**
        1. Upload the front and back of the card.
        2. Download the combined print page.
        """)
    
    with st.expander("Tips for Best Results", expanded=False):
        st.markdown("""
        - **Lighting**: Bright, even lighting
        - **Pose**: Look straight at camera
        - **Expression**: Neutral, mouth closed
        - **Background**: Plain, uniform color
        - **File Format**: JPEG or PNG
        - **Resolution**: At least 640 x 480 pixels
        """)
    
    if document_type == "Passport / Visa photo":
        with st.expander("About Countries", expanded=False):
            for code, spec in specs.items():
                st.write(f"**{code}** - {spec.name}")
                st.write(f"Size: {spec.width_in}\" x {spec.height_in}\"")

