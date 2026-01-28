#!/usr/bin/env python3
"""Streamlit GUI for IDphotoApp - Interactive photo processing interface."""

import streamlit as st
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import io
import tempfile

from process_photo import (
    load_specs,
    detect_face,
    crop_to_spec,
    replace_background,
    get_foreground_mask,
    build_print_sheet,
    LayoutSpec,
    parse_layout,
)

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

# Configure page
st.set_page_config(
    page_title="ID Photo Processor",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main container padding */
    .main {
        padding: 1rem;
    }
    
    /* Header styling */
    h1 {
        text-align: center;
        color: #1f77d4;
        padding-bottom: 1rem;
        border-bottom: 3px solid #1f77d4;
        margin-bottom: 1.5rem;
    }
    
    h2 {
        color: #1f77d4;
        padding-top: 0.5rem;
        border-left: 5px solid #1f77d4;
        padding-left: 1rem;
        margin-top: 1.5rem;
    }
    
    h3 {
        color: #0a4a90;
        margin-top: 1rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f0f5ff;
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
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("📸 ID Photo Processor")
st.markdown("""
<div style="text-align: center; color: #666; margin-bottom: 2rem;">
    <p><strong>Professional Identity Photo Processing</strong></p>
    <p style="font-size: 0.9rem;">Auto-crop, background replacement & print sheet generation</p>
</div>
""", unsafe_allow_html=True)

# Load specs early
specs_path = Path(__file__).resolve().parent / "specs.json"
specs = load_specs(specs_path)

# Show profile requirements
with st.expander("📐 Profile Requirements & Visual Guide", expanded=False):
    col_req1, col_req2, col_req3 = st.columns(3)
    
    with col_req1:
        st.markdown("### ✓ Head to Shoulder Profile")
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
        st.markdown("### 📋 Standards by Country (50+ Countries)")
        
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
        st.markdown("### 🎯 Best Practices")
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
    st.markdown("### 📸 Visual Examples")
    
    col_example1, col_example2 = st.columns(2)
    with col_example1:
        st.markdown("**✓ GOOD PROFILE**")
        # Create simple visual guide
        example_img = np.ones((400, 300, 3), dtype=np.uint8) * 240
        # Head and shoulders outline
        cv2.rectangle(example_img, (50, 30), (250, 280), (50, 150, 50), 3)
        cv2.putText(example_img, "Top of head", (70, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
        cv2.putText(example_img, "Mid-chest", (80, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
        cv2.line(example_img, (150, 150), (150, 150), (100, 200, 100), 3)  # Eyes line
        st.image(Image.fromarray(example_img), use_container_width=True)
    
    with col_example2:
        st.markdown("**✗ COMMON MISTAKES**")
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
    
    # Country selection
    st.markdown("### 🌍 Country Selection")
    country = st.selectbox(
        "Select your country/purpose",
        options=list(specs.keys()),
        format_func=lambda x: specs[x].name,
        help="Choose the country specification and document type for your ID photo",
        label_visibility="collapsed"
    )
    
    # Photo settings
    st.markdown("### 📷 Photo Settings")
    replace_bg = st.checkbox("🧽 Remove/Replace Background", value=False, help="Remove the background and fill with a solid color")
    background_color_options = {
        "Use spec default": None,
        "Transparent (PNG)": "transparent",
        "White": (255, 255, 255),
        "Off-white": (245, 245, 245),
        "Light gray": (230, 230, 230),
        "Blue": (0, 120, 255),
        "Light blue": (200, 220, 255),
    }
    background_color_choice = st.selectbox(
        "Background color",
        options=list(background_color_options.keys()),
        index=0,
        help="Choose a common background color for the final photo",
        disabled=not replace_bg,
    )
    st.markdown("Background tolerance range")
    tol_col1, tol_col2 = st.columns(2)
    with tol_col1:
        tol_min = st.number_input(
            "Min",
            min_value=1,
            max_value=100,
            value=5,
            step=1,
            disabled=not replace_bg,
        )
    with tol_col2:
        tol_max = st.number_input(
            "Max",
            min_value=1,
            max_value=100,
            value=60,
            step=1,
            disabled=not replace_bg,
        )
    if tol_max <= tol_min:
        tol_max = tol_min + 1
    bg_tolerance = st.slider(
        "Background tolerance",
        min_value=int(tol_min),
        max_value=int(tol_max),
        value=int(min(max(25, tol_min), tol_max)),
        step=1,
        help="Higher values remove more background (may eat into the subject).",
        disabled=not replace_bg,
    )
    face_protect = st.slider(
        "Face protection size",
        min_value=0.25,
        max_value=0.6,
        value=0.4,
        step=0.05,
        help="Lower values preserve less area around the face.",
        disabled=not replace_bg,
    )
    dpi = st.slider("🎯 Quality (DPI)", min_value=100, max_value=600, value=300, step=50, help="Higher DPI = Better print quality")
    
    st.divider()
    
    # Layout settings
    st.markdown("### 📄 Print Layout")
    layout_preset = st.radio("Layout Size", ["4x6", "6x6", "Custom"], help="Select your print paper size")
    
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
    
    st.markdown("#### Fine Tuning")
    col_margin, col_spacing = st.columns(2)
    with col_margin:
        st.markdown("Margin (distance from edge)")
        margin = st.number_input("Margin", value=0.02, min_value=0.0, step=0.01, label_visibility="collapsed", help="Distance from paper edges to photos: 0.02\" (very tight), 0.25\" (minimal), 0.5\" (standard)")
    with col_spacing:
        st.markdown("Spacing (between photos)")
        spacing = st.number_input("Spacing", value=0.02, min_value=0.0, step=0.01, label_visibility="collapsed", help="Gap between photos on the sheet")

    st.divider()
    st.markdown("### 🖼️ Display")
    show_guides = st.checkbox(
        "Show crop frames and guide lines",
        value=True,
        help="Toggle crop frames and guide lines on previews (enabled by default for manual mode).",
    )
    show_sheet_guides = st.checkbox("Show print sheet cut lines", value=False, help="Toggle cut lines, outlines, and corner marks on the print sheet")
    show_mask_debug = st.checkbox(
        "Show background mask preview",
        value=False,
        help="Preview the mask: white = kept (foreground), black = removed (background).",
    )
    
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.85rem; padding: 1rem 0;">
        <p>💡 <strong>Tip:</strong> Manual mode lets you fine-tune the crop area</p>
    </div>
    """, unsafe_allow_html=True)

# Main content area
st.markdown("---")
col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.markdown("### 📤 Upload Your Photo")
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=["jpg", "jpeg", "png"],
        help="Upload a clear, front-facing photo (JPG or PNG)",
        label_visibility="collapsed"
    )

with col2:
    st.markdown("### 📊 File Information")
    if uploaded_file:
        st.success(f"✓ File uploaded: **{uploaded_file.name}**")
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.info(f"📁 Size: {file_size_mb:.2f} MB")
    else:
        st.info("👆 Upload a photo to get started")

# Process photo if uploaded
if uploaded_file:
    try:
        # Read the uploaded image
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if image_bgr is None:
            st.error("❌ Could not read image. Please upload a valid image file.")
        else:
            # Show processing mode selection
            st.markdown("---")
            st.markdown("### 🎯 Processing Mode")
            
            mode_col1, mode_col2 = st.columns(2)
            with mode_col1:
                if st.button("⚡ Automatic (AI Detection)", use_container_width=True, key="auto_mode_btn"):
                    st.session_state.processing_mode = "Automatic"
            with mode_col2:
                if st.button("✏️ Manual (Fine-Tune)", use_container_width=True, key="manual_mode_btn"):
                    st.session_state.processing_mode = "Manual Adjustment"
            
            processing_mode = st.session_state.get("processing_mode", "Automatic")
            
            with st.spinner("Processing..."):
                transparent_bg = replace_bg and (background_color_choice == "Transparent (PNG)")
                background_rgb = background_color_options.get(background_color_choice)
                if background_rgb in (None, "transparent"):
                    background_rgb = specs[country].background_rgb
                pad_rgb = background_rgb if replace_bg else specs[country].background_rgb
                
                # Detect face
                bbox, eye_point = detect_face(image_bgr)

                # Replace background if selected
                if replace_bg and not transparent_bg:
                    image_bgr = replace_background(
                        image_bgr,
                        background_rgb,
                        face_bbox=bbox,
                        bbox_expand_x=0.4,
                        bbox_expand_y=0.6,
                        bg_tolerance=float(bg_tolerance),
                        face_protect=float(face_protect),
                    )
                
                # Crop to spec
                cropped_bgr = crop_to_spec(image_bgr, bbox, eye_point, specs[country], dpi, background_rgb=pad_rgb)

                # If background replacement is enabled, re-apply on the cropped image so the result is visible
                if replace_bg and not transparent_bg:
                    try:
                        bbox_cropped, _ = detect_face(cropped_bgr)
                    except Exception:
                        bbox_cropped = None
                    cropped_bgr = replace_background(
                        cropped_bgr,
                        background_rgb,
                        face_bbox=bbox_cropped,
                        bbox_expand_x=0.2,
                        bbox_expand_y=0.3,
                        bg_tolerance=float(bg_tolerance),
                        face_protect=float(face_protect),
                    )
                
                # Optional debug mask preview
                if replace_bg and show_mask_debug:
                    with st.expander("Background Mask Preview", expanded=True):
                        dbg_col1, dbg_col2 = st.columns(2)
                        with dbg_col1:
                            try:
                                mask_orig = get_foreground_mask(
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
                                mask_crop = get_foreground_mask(
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
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 0.5rem; color: white; text-align: center;">
                    <h2 style="color: white; border: none; margin-top: 0;">📐 Manual Crop Adjustment</h2>
                    <p style="color: #f0f0f0; margin: 0;">Head & Shoulder Profile Framing</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("""
                **Your Goal**: Position the crop frame to capture head and shoulders correctly.  
                Use the controls below to fine-tune the crop area to perfection.
                """)
                
                # Show visual guide and instructions
                tab1, tab2 = st.tabs(["Instructions", "Visual Guide"])
                
                with tab1:
                    col_instr1, col_instr2 = st.columns(2)
                    with col_instr1:
                        st.markdown("### ✓ Correct Framing")
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
                        st.markdown("### ✗ Common Mistakes")
                        st.markdown("""
                        **To Avoid:**
                        - ❌ Cutting off top of head
                        - ❌ Too much forehead
                        - ❌ Tilted head
                        - ❌ Shoulders cut off
                        - ❌ Too much upper body
                        - ❌ Uneven side framing
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
                st.markdown("### 🎯 Manual Crop Controls")
                st.markdown("*Use the buttons below to resize and move the crop frame.*")
                
                # Compute defaults optimized for target photo format
                h, w = image_bgr.shape[:2]
                image_aspect_ratio = w / h
                
                # Get target photo specifications
                spec = specs[country]
                target_aspect_ratio = spec.width_in / spec.height_in
                target_eye_pos = spec.eye_line_from_bottom_ratio
                target_head_fill = spec.head_height_ratio
                
                # Calculate default crop frame optimized for the target format
                try:
                    # Center the crop frame in the image
                    center_y_pct = 50
                    center_x_pct = 50
                    
                    # Calculate frame height based on target head fill ratio
                    # Frame should accommodate head at the specified position
                    frame_height_pct = target_head_fill * 100 / 0.7  # Add padding above/below head
                    frame_height_pct = min(80, frame_height_pct)  # Cap at 80% of image
                    
                    # Calculate frame width to match target aspect ratio
                    frame_width_pct = frame_height_pct * target_aspect_ratio
                    frame_width_pct = min(80, frame_width_pct)  # Cap at 80% of image
                    
                    # Position vertically so eyes are at the target position
                    default_top = max(5, int(center_y_pct - frame_height_pct * (1 - target_eye_pos)))
                    default_bottom = min(95, int(center_y_pct + frame_height_pct * target_eye_pos))
                    
                    # Position horizontally centered
                    default_left = max(10, int(center_x_pct - frame_width_pct / 2))
                    default_right = min(90, int(center_x_pct + frame_width_pct / 2))
                    
                except:
                    # Fallback defaults
                    default_top, default_bottom = 20, 80
                    default_left, default_right = 20, 80
                
                # Use original image without zoom
                image_zoomed = image_bgr.copy()
                h_zoom, w_zoom = image_zoomed.shape[:2]
                
                # Create a compact control panel
                st.markdown("### 🎯 Crop Controls - Adjust to Tolerance Zones")
                
                # Main layout: key parameters only
                st.markdown("*Use these controls to position your photo within the tolerance zones (colored bands)*")
                
                # Tolerance for guide/validation bands (±15% of crop height)
                tolerance = 0.15
                
                # Size and Position controls
                size_pos_col1, size_pos_col2 = st.columns(2, gap="medium")
                
                with size_pos_col1:
                    st.markdown("#### 📏 Crop Size")
                    size_btn_col1, size_btn_col2 = st.columns(2, gap="small")
                    with size_btn_col1:
                        if st.button("➖ Shrink", key="shrink_crop", help="Shrink crop area by 15%", use_container_width=True):
                            st.session_state.scale_factor = getattr(st.session_state, 'scale_factor', 1.0) - 0.15
                    with size_btn_col2:
                        if st.button("➕ Enlarge", key="enlarge_crop", help="Enlarge crop area by 15%", use_container_width=True):
                            st.session_state.scale_factor = getattr(st.session_state, 'scale_factor', 1.0) + 0.15
                    
                    scale_display = getattr(st.session_state, 'scale_factor', 1.0)
                    st.metric("Scale Factor", f"{scale_display:.0%}", delta=None)
                    
                    if st.button("🔄 Reset Size", key="reset_crop", use_container_width=True, help="Reset to default size"):
                        st.session_state.scale_factor = 1.0
                
                with size_pos_col2:
                    st.markdown("#### ➡️ Crop Position")
                    
                    # Up button
                    if st.button("⬆️ UP", key="move_up", use_container_width=True, help="Move up by 2%"):
                        st.session_state.move_offset_y = getattr(st.session_state, 'move_offset_y', 0) - 2
                    
                    # Left/Right row
                    dir_col1, dir_col2 = st.columns(2, gap="small")
                    with dir_col1:
                        if st.button("⬅️ LEFT", key="move_left", use_container_width=True, help="Move left by 2%"):
                            st.session_state.move_offset_x = getattr(st.session_state, 'move_offset_x', 0) - 2
                    with dir_col2:
                        if st.button("RIGHT ➡️", key="move_right", use_container_width=True, help="Move right by 2%"):
                            st.session_state.move_offset_x = getattr(st.session_state, 'move_offset_x', 0) + 2
                    
                    # Down button
                    if st.button("⬇️ DOWN", key="move_down", use_container_width=True, help="Move down by 2%"):
                        st.session_state.move_offset_y = getattr(st.session_state, 'move_offset_y', 0) + 2
                    
                    move_x = getattr(st.session_state, 'move_offset_x', 0)
                    move_y = getattr(st.session_state, 'move_offset_y', 0)
                    st.metric("Position", f"({move_x:+d}%, {move_y:+d}%)", delta=None)
                    
                    if st.button("🔄 Reset Pos", key="reset_pos", use_container_width=True, help="Reset to center"):
                        st.session_state.move_offset_x = 0
                        st.session_state.move_offset_y = 0
                
                # Apply scale factor from +/- buttons
                scale_factor = getattr(st.session_state, 'scale_factor', 1.0)
                scale_factor = max(0.5, min(2.0, scale_factor))  # Clamp between 0.5x and 2.0x
                
                # Get movement offsets from directional buttons
                move_offset_x = getattr(st.session_state, 'move_offset_x', 0)
                move_offset_y = getattr(st.session_state, 'move_offset_y', 0)
                
                # Use default crop boundaries based on spec
                spec = specs[country]
                crop_top_pct = max(5, int((1 - spec.eye_line_from_bottom_ratio - spec.head_height_ratio/2) * 100))
                crop_bottom_pct = min(95, int((1 - spec.eye_line_from_bottom_ratio + spec.head_height_ratio/2) * 100))
                crop_left_pct = 15
                crop_right_pct = 85
                
                # Calculate scaled crop boundaries
                # Center the crop area and scale it
                center_y = (crop_top_pct + crop_bottom_pct) / 2
                center_x = (crop_left_pct + crop_right_pct) / 2
                
                height_range = crop_bottom_pct - crop_top_pct
                width_range = crop_right_pct - crop_left_pct
                
                # Apply scale factor and lock to target aspect ratio
                scaled_height = height_range * scale_factor
                target_aspect = spec.width_in / spec.height_in
                scaled_width = scaled_height * target_aspect * (h_zoom / w_zoom)
                if scaled_width > 100:
                    scaled_width = 100
                    scaled_height = scaled_width / (target_aspect * (h_zoom / w_zoom))
                if scaled_height > 100:
                    scaled_height = 100
                    scaled_width = scaled_height * target_aspect * (h_zoom / w_zoom)
                
                # Apply movement offset to center (clamped to keep frame inside bounds)
                half_h = scaled_height / 2
                half_w = scaled_width / 2
                center_y_moved = min(max(center_y + move_offset_y, half_h), 100 - half_h)
                center_x_moved = min(max(center_x + move_offset_x, half_w), 100 - half_w)
                
                # Keep within bounds with correct aspect ratio
                crop_top_pct_scaled = center_y_moved - half_h
                crop_bottom_pct_scaled = center_y_moved + half_h
                crop_left_pct_scaled = center_x_moved - half_w
                crop_right_pct_scaled = center_x_moved + half_w
                
                # Apply manual crop on zoomed image with scaled and moved boundaries
                y1 = int(h_zoom * crop_top_pct_scaled / 100)
                y2 = int(h_zoom * crop_bottom_pct_scaled / 100)
                x1 = int(w_zoom * crop_left_pct_scaled / 100)
                x2 = int(w_zoom * crop_right_pct_scaled / 100)
                
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
                
                # Validate feature positioning with tolerance
                crop_h = y2 - y1
                
                # Check if key features are within acceptable bounds
                eye_line_y = y1 + int(crop_h * (1 - spec.eye_line_from_bottom_ratio))
                forehead_y = y1 + int(crop_h * 0.1)
                shoulders_y = y2 - int(crop_h * 0.15)
                head_top_y = y1 + int(crop_h * 0.05)
                
                # Tolerance ranges (±15% of crop area)
                eye_in_frame = y1 < eye_line_y < y2
                forehead_in_frame = y1 - int(crop_h * tolerance) <= forehead_y <= y1 + int(crop_h * tolerance)
                shoulders_in_frame = y2 - int(crop_h * tolerance) <= shoulders_y <= y2 + int(crop_h * tolerance)
                head_top_in_frame = y1 - int(crop_h * tolerance) <= head_top_y <= y1 + int(crop_h * tolerance)
                center_aligned = abs(x2 - x1 - crop_w) < int(crop_w * tolerance)
                
                # Overall validation
                features_valid = all([eye_in_frame, forehead_in_frame, shoulders_in_frame, head_top_in_frame, center_aligned])
                
                # Show live preview (optional overlay)
                st.markdown("### 📸 Live Preview")
                if show_guides:
                    st.markdown("*Green box shows the area that will be cropped. Guide lines help position key features correctly.*")
                
                col_preview1, col_preview2 = st.columns(2)
                with col_preview1:
                    if show_guides:
                        # Draw rectangle showing crop area on zoomed image
                        img_display = image_zoomed.copy()
                        
                        # Draw outer rectangle with a thinner border
                        cv2.rectangle(img_display, (x1, y1), (x2, y2), (0, 200, 0), 2)
                        
                        # Add guide lines for correct positioning
                        crop_h = y2 - y1
                        crop_w = x2 - x1
                        tolerance_px = int(crop_h * tolerance)
                        
                        # Top of head guide
                        head_top_y = y1 + int(crop_h * 0.05)
                        head_top_zone_top = max(y1, head_top_y - tolerance_px)
                        head_top_zone_bottom = head_top_y + tolerance_px
                        cv2.line(img_display, (x1, head_top_zone_top), (x2, head_top_zone_top), (170, 170, 170), 1)
                        cv2.line(img_display, (x1, head_top_y), (x2, head_top_y), (150, 150, 150), 1)
                        cv2.line(img_display, (x1, head_top_zone_bottom), (x2, head_top_zone_bottom), (170, 170, 170), 1)
                        cv2.putText(img_display, "Head Top", (x1 + 5, head_top_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
                        
                        # Eye line tolerance zone
                        eye_line_y = y1 + int(crop_h * (1 - specs[country].eye_line_from_bottom_ratio))
                        eye_top = eye_line_y - tolerance_px
                        eye_bottom = eye_line_y + tolerance_px
                        cv2.line(img_display, (x1, eye_top), (x2, eye_top), (180, 180, 180), 1)
                        cv2.line(img_display, (x1, eye_line_y), (x2, eye_line_y), (160, 160, 160), 1)
                        cv2.line(img_display, (x1, eye_bottom), (x2, eye_bottom), (180, 180, 180), 1)
                        cv2.putText(img_display, "Eyes", (x1 + 5, eye_line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (160, 160, 160), 1)
                        
                        # Shoulders / mid-chest guide (bottom)
                        shoulders_y = y2 - int(crop_h * 0.15)
                        shoulders_top = shoulders_y - tolerance_px
                        shoulders_bottom = min(y2, shoulders_y + tolerance_px)
                        cv2.line(img_display, (x1, shoulders_top), (x2, shoulders_top), (170, 170, 170), 1)
                        cv2.line(img_display, (x1, shoulders_y), (x2, shoulders_y), (150, 150, 150), 1)
                        cv2.line(img_display, (x1, shoulders_bottom), (x2, shoulders_bottom), (170, 170, 170), 1)
                        cv2.putText(img_display, "Shoulders", (x1 + 5, shoulders_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
                        
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
                    st.caption(f"📐 Crop: {crop_w}×{crop_h} px | Scale: {scale_factor:.0%} | Pos: ({move_offset_x:+d}%, {move_offset_y:+d}%)")
                    
                    # Show feature validation status
                    st.markdown("#### ✓ Feature Position Validation")
                    val_col1, val_col2, val_col3 = st.columns(3)
                    with val_col1:
                        if forehead_in_frame:
                            st.success("✓ Forehead", icon="✅")
                        else:
                            st.warning("✗ Forehead", icon="⚠️")
                    with val_col2:
                        if eye_in_frame:
                            st.success("✓ Eyes", icon="✅")
                        else:
                            st.warning("✗ Eyes", icon="⚠️")
                    with val_col3:
                        if head_top_in_frame:
                            st.success("✓ Head Top", icon="✅")
                        else:
                            st.warning("✗ Head Top", icon="⚠️")
                    
                    val_col4, val_col5 = st.columns(2)
                    with val_col4:
                        if shoulders_in_frame:
                            st.success("✓ Shoulders", icon="✅")
                        else:
                            st.warning("✗ Shoulders", icon="⚠️")
                    with val_col5:
                        if center_aligned:
                            st.success("✓ Centered", icon="✅")
                        else:
                            st.warning("✗ Centered", icon="⚠️")
                    
                    # Overall validation status
                    if features_valid:
                        st.success("🎉 All features in correct position! Ready to save.", icon="✅")
                    else:
                        st.info("📍 Adjust the crop frame to position all features correctly", icon="ℹ️")
                
                with col_preview2:
                    # Display final photo (optional guide overlay)
                    final_photo_display = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
                    if show_guides:
                        # Add guide lines to final photo as well (Head Top / Eyes / Shoulders)
                        final_display = final_photo_display.copy()
                        final_h, final_w = final_display.shape[:2]
                        tolerance_px_final = int(final_h * tolerance)
                        
                        # Top of head guide
                        head_top_final = int(final_h * 0.05)
                        head_top_zone_top = max(0, head_top_final - tolerance_px_final)
                        head_top_zone_bottom = head_top_final + tolerance_px_final
                        cv2.line(final_display, (0, head_top_zone_top), (final_w, head_top_zone_top), (170, 170, 170), 1)
                        cv2.line(final_display, (0, head_top_final), (final_w, head_top_final), (150, 150, 150), 1)
                        cv2.line(final_display, (0, head_top_zone_bottom), (final_w, head_top_zone_bottom), (170, 170, 170), 1)
                        cv2.putText(final_display, "Head Top", (5, head_top_final - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
                        
                        # Eye line tolerance zone
                        eye_line_final = int(final_h * (1 - specs[country].eye_line_from_bottom_ratio))
                        eye_top_final = eye_line_final - tolerance_px_final
                        eye_bottom_final = eye_line_final + tolerance_px_final
                        cv2.line(final_display, (0, eye_top_final), (final_w, eye_top_final), (180, 180, 180), 1)
                        cv2.line(final_display, (0, eye_line_final), (final_w, eye_line_final), (160, 160, 160), 1)
                        cv2.line(final_display, (0, eye_bottom_final), (final_w, eye_bottom_final), (180, 180, 180), 1)
                        cv2.putText(final_display, "Eyes", (5, eye_line_final - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (160, 160, 160), 1)
                        
                        # Shoulders / mid-chest guide (bottom)
                        shoulders_final = int(final_h * 0.85)
                        shoulders_top_final = shoulders_final - tolerance_px_final
                        shoulders_bottom_final = min(final_h, shoulders_final + tolerance_px_final)
                        cv2.line(final_display, (0, shoulders_top_final), (final_w, shoulders_top_final), (170, 170, 170), 1)
                        cv2.line(final_display, (0, shoulders_final), (final_w, shoulders_final), (150, 150, 150), 1)
                        cv2.line(final_display, (0, shoulders_bottom_final), (final_w, shoulders_bottom_final), (170, 170, 170), 1)
                        cv2.putText(final_display, "Shoulders", (5, shoulders_final + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
                        
                        st.image(Image.fromarray(final_display), 
                                caption="Final ID Photo with Guides",
                                use_container_width=True)
                    else:
                        st.image(Image.fromarray(final_photo_display), 
                                caption="Final ID Photo",
                                use_container_width=True)
                st.caption(f"✓ {w_px:,} × {h_px:,} px | {specs[country].width_in}\" × {specs[country].height_in}\" @ {dpi} DPI")
            
            # Generate print sheet (for both automatic and manual modes)
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
            sheet = build_print_sheet(
                photo=sheet_photo,
                layout=layout,
                dpi=dpi,
                margin_in=margin,
                spacing_in=spacing,
                copies=effective_copies,
                draw_guides=show_sheet_guides,
            )
            
            # Display results
            st.success("✅ Photo processed successfully!")
            
            col_photo, col_sheet = st.columns(2)
            
            with col_photo:
                st.subheader("Cropped Photo")
                spec = specs[country]
                w_in, h_in = spec.width_in, spec.height_in
                
                # If transparent background requested, build RGBA output for display/download
                if transparent_bg:
                    try:
                        bbox_cropped, _ = detect_face(cropped_bgr)
                    except Exception:
                        bbox_cropped = None
                    fg_mask = get_foreground_mask(
                        cropped_bgr,
                        face_bbox=bbox_cropped,
                        bbox_expand_x=0.2,
                        bbox_expand_y=0.3,
                        prefer_white_key=False,
                        bg_tolerance=float(bg_tolerance),
                    )
                    # Be conservative for transparency: grow the foreground a bit and soften edges.
                    fg_mask = cv2.dilate(
                        fg_mask,
                        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
                        iterations=2,
                    )
                    fg_mask = cv2.morphologyEx(
                        fg_mask,
                        cv2.MORPH_CLOSE,
                        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
                        iterations=2,
                    )
                    # Fill small holes inside the foreground mask.
                    inv = cv2.bitwise_not(fg_mask)
                    h_m, w_m = inv.shape[:2]
                    flood = inv.copy()
                    mask = np.zeros((h_m + 2, w_m + 2), np.uint8)
                    cv2.floodFill(flood, mask, (0, 0), 255)
                    holes = cv2.bitwise_not(flood)
                    fg_mask = cv2.bitwise_or(fg_mask, holes)
                    fg_mask = cv2.GaussianBlur(fg_mask, (5, 5), 0)

                    # Final hard-protect: keep only the core face ellipse to prevent erosion.
                    if bbox_cropped is not None:
                        x, y, w, h = bbox_cropped
                        # Also force an ellipse over the core face area.
                        cx = x + w // 2
                        cy = y + h // 2
                        axes = (int(w * face_protect), int(h * (face_protect + 0.15)))
                        face_core = np.zeros_like(fg_mask)
                        cv2.ellipse(face_core, (cx, cy), axes, 0, 0, 360, 255, -1)
                        fg_mask = cv2.bitwise_or(fg_mask, face_core)
                    if float(np.mean(fg_mask > 0)) > 0.98:
                        b, g, r = cv2.split(cropped_bgr)
                        white_mask = (b > 235) & (g > 235) & (r > 235)
                        fg_mask = (~white_mask).astype(np.uint8) * 255
                    rgba = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGBA)
                    rgba[:, :, 3] = fg_mask
                    cropped_pil = Image.fromarray(rgba)
                
                # Display cropped photo without text overlay
                if transparent_bg:
                    st.image(cropped_pil, caption=f"{w_in}\" × {h_in}\" (transparent)", use_container_width=True)
                else:
                    cropped_display = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
                    st.image(Image.fromarray(cropped_display), caption=f"{w_in}\" × {h_in}\"", use_container_width=True)
                
                # Photo size info
                w_px, h_px = cropped_pil.size
                st.caption(f"📐 Size: {w_px:,} × {h_px:,} px @ {dpi} DPI | {country} Standard")
                
                # Download cropped photo
                img_buffer = io.BytesIO()
                cropped_pil.save(img_buffer, format="PNG")
                download_name = f"{country.lower()}_photo.png"
                download_mime = "image/png"
                img_buffer.seek(0)
                
                st.download_button(
                    label="📥 Download Photo",
                    data=img_buffer,
                    file_name=download_name,
                    mime=download_mime,
                    use_container_width=True
                )
            
            with col_sheet:
                st.subheader("Print Sheet")
                
                # Display print sheet without text overlay
                sheet_display = cv2.cvtColor(np.array(sheet), cv2.COLOR_RGB2BGR)
                sheet_display_rgb = cv2.cvtColor(sheet_display, cv2.COLOR_BGR2RGB)
                st.image(Image.fromarray(sheet_display_rgb), caption=f"Print Layout: {layout.width_in}\" × {layout.height_in}\"", use_container_width=True)
                
                # Sheet size info
                sheet_w, sheet_h = sheet.size
                st.caption(f"📐 Sheet: {sheet_w:,} × {sheet_h:,} px @ {dpi} DPI | {effective_copies} copies")
                
                # Download print sheet
                sheet_buffer = io.BytesIO()
                sheet.save(sheet_buffer, format="JPEG", quality=95)
                sheet_buffer.seek(0)
                
                st.download_button(
                    label="📥 Download Sheet",
                    data=sheet_buffer,
                    file_name=f"{country.lower()}_sheet_{int(layout.width_in)}x{int(layout.height_in)}.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )
            
            # Specifications display
            st.subheader("Specifications Used")
            col_specs1, col_specs2, col_specs3 = st.columns(3)
            
            with col_specs1:
                st.metric("Country", f"{country} - {specs[country].name}")
            
            with col_specs2:
                st.metric("Photo Size", f"{specs[country].width_in}\" × {specs[country].height_in}\"")
            
            with col_specs3:
                st.metric("Head Frame Coverage", f"{specs[country].head_height_ratio:.0%}")
    
    except RuntimeError as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("💡 Try: Clear photo, good lighting, front-facing pose")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        st.info("📝 Please check that your image is valid and properly formatted")

# Instructions sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("📖 How to Use")
    with st.expander("Setup", expanded=False):
        st.markdown("""
        1. Select your country
        2. Configure settings (DPI, layout, etc.)
        3. Upload a photo
        4. Download the results
        """)
    
    with st.expander("Tips for Best Results", expanded=False):
        st.markdown("""
        - **Lighting**: Bright, even lighting
        - **Pose**: Look straight at camera
        - **Expression**: Neutral, mouth closed
        - **Background**: Plain, uniform color
        - **File Format**: JPEG or PNG
        - **Resolution**: At least 640×480 pixels
        """)
    
    with st.expander("About Countries", expanded=False):
        for code, spec in specs.items():
            st.write(f"**{code}** - {spec.name}")
            st.write(f"Size: {spec.width_in}\" × {spec.height_in}\"")
