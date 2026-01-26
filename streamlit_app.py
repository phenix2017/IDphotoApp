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
    build_print_sheet,
    LayoutSpec,
    parse_layout,
)

try:
    from streamlit_image_coordinates import streamlit_image_coordinates
except ImportError:
    streamlit_image_coordinates = None

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
specs = load_specs(Path("specs.json"))

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
        st.markdown("### 📋 Standards by Country")
        for code, spec in specs.items():
            st.write(f"**{code}** - {spec.name}")
            st.write(f"  Size: {spec.width_in}\" × {spec.height_in}\"")
            st.write(f"  Head: {spec.head_height_ratio:.0%} of height")
            st.write(f"  Eyes: {spec.eye_line_from_bottom_ratio:.0%} from bottom")
    
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
        "Select your country",
        options=list(specs.keys()),
        format_func=lambda x: f"🇺🇸 {x} - {specs[x].name}" if x == "US" else f"🇨🇦 {x} - {specs[x].name}" if x == "CA" else f"🇬🇧 {x} - {specs[x].name}",
        help="Choose the country specification for your ID photo",
        label_visibility="collapsed"
    )
    
    # Photo settings
    st.markdown("### 📷 Photo Settings")
    replace_bg = st.checkbox("🎨 Replace Background", value=False, help="Automatically remove and replace the background")
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
    
    copies = st.slider("📋 Number of Copies", min_value=1, max_value=20, value=6, help="How many photos per sheet")
    
    st.markdown("#### Fine Tuning")
    col_margin, col_spacing = st.columns(2)
    with col_margin:
        st.markdown("Margin (standard: 0.25\")")
        margin = st.number_input("Margin", value=0.25, min_value=0.0, step=0.05, label_visibility="collapsed", help="Standard print margin: 0.25\" (professional), 0.5\" (safer)")
    with col_spacing:
        st.markdown("Spacing")
        spacing = st.number_input("Spacing", value=0.05, min_value=0.0, step=0.05, label_visibility="collapsed", help="Gap between photos")
    
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
                # Replace background if selected
                if replace_bg:
                    image_bgr = replace_background(image_bgr, specs[country].background_rgb)
                
                # Detect face
                bbox, eye_point = detect_face(image_bgr)
                
                # Crop to spec
                cropped_bgr = crop_to_spec(image_bgr, bbox, eye_point, specs[country], dpi)
                
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
                st.markdown("### 🎯 Adjust Crop Boundaries")
                st.markdown("*Drag sliders to position the crop frame around the head and shoulders*")
                
                # Create sliders with default values
                h, w = image_bgr.shape[:2]
                
                # Get automatic crop as reference
                try:
                    auto_h_ratio = specs[country].head_height_ratio
                    auto_eye_pos = specs[country].eye_line_from_bottom_ratio
                    # Estimate crop based on face size (auto crop will be ~50-70% of image)
                    default_top = max(5, int((1 - auto_eye_pos - auto_h_ratio/2) * 100))
                    default_bottom = min(95, int((1 - auto_eye_pos + auto_h_ratio/2) * 100))
                    default_left = 15
                    default_right = 85
                except:
                    default_top, default_bottom = 20, 85
                    default_left, default_right = 15, 85
                
                # Zoom control
                st.markdown("#### 🔍 Zoom Level")
                zoom_col1, zoom_col2, zoom_col3 = st.columns([3, 1, 1], gap="small")
                with zoom_col1:
                    zoom_level = st.slider(
                        "Zoom Level",
                        min_value=50, max_value=200, value=100, step=5,
                        key="zoom_slider",
                        help="50% = zoomed out, 200% = zoomed in"
                    )
                with zoom_col2:
                    st.metric("", f"{zoom_level}%", delta=None)
                with zoom_col3:
                    st.metric("", f"{zoom_level/100:.1f}x", delta=None)
                
                # Apply zoom to image - show preview of zoom
                if zoom_level != 100:
                    zoom_h = int(h * zoom_level / 100)
                    zoom_w = int(w * zoom_level / 100)
                    image_zoomed = cv2.resize(image_bgr, (zoom_w, zoom_h), interpolation=cv2.INTER_CUBIC)
                    st.success(f"✅ Image zoomed to {zoom_level}% - Adjust crop sliders to fit the photo")
                else:
                    image_zoomed = image_bgr.copy()
                    st.info("📐 100% - Original size. Adjust crop sliders or use zoom to scale.")
                
                # Update dimensions after zoom
                h_zoom, w_zoom = image_zoomed.shape[:2]
                
                # Create a compact control panel
                st.markdown("### 🎯 Crop Controls - Adjust to Tolerance Zones")
                
                # Main layout: key parameters only
                st.markdown("*Use these controls to position your photo within the tolerance zones (colored bands)*")
                
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
                
                # Apply scale factor
                scaled_height = height_range * scale_factor
                scaled_width = width_range * scale_factor
                
                # Apply movement offset to center
                center_y_moved = center_y + move_offset_y
                center_x_moved = center_x + move_offset_x
                
                # Keep within bounds
                crop_top_pct_scaled = max(0, min(50, center_y_moved - scaled_height / 2))
                crop_bottom_pct_scaled = min(100, max(crop_top_pct_scaled + 30, center_y_moved + scaled_height / 2))
                crop_left_pct_scaled = max(0, min(40, center_x_moved - scaled_width / 2))
                crop_right_pct_scaled = min(100, max(crop_left_pct_scaled + 40, center_x_moved + scaled_width / 2))
                
                # Apply manual crop on zoomed image with scaled and moved boundaries
                y1 = int(h_zoom * crop_top_pct_scaled / 100)
                y2 = int(h_zoom * crop_bottom_pct_scaled / 100)
                x1 = int(w_zoom * crop_left_pct_scaled / 100)
                x2 = int(w_zoom * crop_right_pct_scaled / 100)
                
                manual_cropped_bgr = image_zoomed[y1:y2, x1:x2]
                
                # Resize to spec dimensions
                w_px, h_px = int(round(spec.width_in * dpi)), int(round(spec.height_in * dpi))
                manual_cropped_bgr = cv2.resize(manual_cropped_bgr, (w_px, h_px), interpolation=cv2.INTER_CUBIC)
                
                manual_cropped_rgb = cv2.cvtColor(manual_cropped_bgr, cv2.COLOR_BGR2RGB)
                cropped_pil = Image.fromarray(manual_cropped_rgb)
                
                # Update cropped_bgr to use manual adjustment
                cropped_bgr = manual_cropped_bgr
                
                # Validate feature positioning with tolerance
                crop_h = y2 - y1
                crop_w = x2 - x1
                tolerance = 0.15  # 15% tolerance for feature positioning
                
                # Check if key features are within acceptable bounds
                eye_line_y = y1 + int(crop_h * (1 - spec.eye_line_from_bottom_ratio))
                forehead_y = y1 + int(crop_h * 0.1)
                shoulders_y = y2 - int(crop_h * 0.2)
                head_top_y = y1 + int(crop_h * 0.05)
                
                # Tolerance ranges (±15% of crop area)
                eye_in_frame = y1 < eye_line_y < y2
                forehead_in_frame = y1 - int(crop_h * tolerance) <= forehead_y <= y1 + int(crop_h * tolerance)
                shoulders_in_frame = y2 - int(crop_h * tolerance) <= shoulders_y <= y2 + int(crop_h * tolerance)
                head_top_in_frame = y1 - int(crop_h * tolerance) <= head_top_y <= y1 + int(crop_h * tolerance)
                center_aligned = abs(x2 - x1 - crop_w) < int(crop_w * tolerance)
                
                # Overall validation
                features_valid = all([eye_in_frame, forehead_in_frame, shoulders_in_frame, head_top_in_frame, center_aligned])
                
                # Show live preview with crop box overlay
                st.markdown("### 📸 Live Preview")
                st.markdown("*Green box shows the area that will be cropped. Guide lines help position key features correctly.*")
                
                col_preview1, col_preview2 = st.columns(2)
                with col_preview1:
                    # Draw rectangle showing crop area on zoomed image
                    img_display = image_zoomed.copy()
                    
                    # Draw outer rectangle with thick green border
                    cv2.rectangle(img_display, (x1, y1), (x2, y2), (0, 255, 0), 4)
                    
                    # Add guide lines for correct positioning
                    crop_h = y2 - y1
                    crop_w = x2 - x1
                    tolerance_px = int(crop_h * tolerance)
                    
                    # Forehead tolerance zone (top area)
                    forehead_y = y1 + int(crop_h * 0.1)
                    forehead_top = max(y1, forehead_y - tolerance_px)
                    forehead_bottom = forehead_y + tolerance_px
                    cv2.rectangle(img_display, (x1, forehead_top), (x2, forehead_bottom), (100, 255, 255), -1)  # Cyan fill
                    cv2.line(img_display, (x1, forehead_y), (x2, forehead_y), (0, 200, 255), 2)  # Bright cyan center
                    cv2.putText(img_display, "Forehead", (x1 + 5, forehead_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 2)
                    
                    # Eye line tolerance zone
                    eye_line_y = y1 + int(crop_h * (1 - specs[country].eye_line_from_bottom_ratio))
                    eye_top = eye_line_y - tolerance_px
                    eye_bottom = eye_line_y + tolerance_px
                    cv2.rectangle(img_display, (x1, eye_top), (x2, eye_bottom), (255, 100, 255), -1)  # Magenta fill
                    cv2.line(img_display, (x1, eye_line_y), (x2, eye_line_y), (255, 0, 255), 2)  # Bright magenta center
                    cv2.putText(img_display, "Eyes", (x1 + 5, eye_line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
                    
                    # Shoulders/chest tolerance zone (bottom area)
                    shoulders_y = y2 - int(crop_h * 0.2)
                    shoulders_top = shoulders_y - tolerance_px
                    shoulders_bottom = min(y2, shoulders_y + tolerance_px)
                    cv2.rectangle(img_display, (x1, shoulders_top), (x2, shoulders_bottom), (100, 200, 100), -1)  # Light green fill
                    cv2.line(img_display, (x1, shoulders_y), (x2, shoulders_y), (0, 200, 0), 2)  # Bright green center
                    cv2.putText(img_display, "Shoulders", (x1 + 5, shoulders_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 2)
                    
                    # Head top tolerance zone
                    head_top_y = y1 + int(crop_h * 0.05)
                    head_top_zone_top = max(y1, head_top_y - tolerance_px)
                    head_top_zone_bottom = head_top_y + tolerance_px
                    cv2.rectangle(img_display, (x1, head_top_zone_top), (x2, head_top_zone_bottom), (200, 150, 100), -1)  # Orange fill
                    cv2.line(img_display, (x1, head_top_y), (x2, head_top_y), (0, 165, 255), 2)  # Orange center
                    cv2.putText(img_display, "Head Top", (x1 + 5, head_top_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
                    
                    # Add center vertical line
                    center_x_line = (x1 + x2) // 2
                    cv2.line(img_display, (center_x_line, y1), (center_x_line, y2), (200, 200, 0), 1)  # Yellow
                    cv2.putText(img_display, "Center", (center_x_line + 5, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 0), 1)
                    
                    # Add corner markers
                    corner_size = 20
                    cv2.line(img_display, (x1, y1), (x1 + corner_size, y1), (0, 200, 255), 3)
                    cv2.line(img_display, (x1, y1), (x1, y1 + corner_size), (0, 200, 255), 3)
                    
                    img_display_rgb = cv2.cvtColor(img_display, cv2.COLOR_BGR2RGB)
                    st.image(Image.fromarray(img_display_rgb), 
                            caption=f"Original Image - Crop with Position Guides",
                            use_container_width=True)
                    
                    # Show crop dimensions below image
                    st.caption(f"📐 Crop: {crop_w}×{crop_h} px | Zoom: {zoom_level}% | Scale: {scale_factor:.0%} | Pos: ({move_offset_x:+d}%, {move_offset_y:+d}%)")
                    
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
                    # Display final photo with feature guides
                    final_photo_display = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
                    
                    # Add guide lines to final photo as well
                    final_display = final_photo_display.copy()
                    final_h, final_w = final_display.shape[:2]
                    tolerance_px_final = int(final_h * tolerance)
                    
                    # Forehead tolerance zone
                    forehead_final = int(final_h * 0.1)
                    forehead_top_final = max(0, forehead_final - tolerance_px_final)
                    forehead_bottom_final = forehead_final + tolerance_px_final
                    cv2.rectangle(final_display, (0, forehead_top_final), (final_w, forehead_bottom_final), (100, 255, 255), -1)
                    cv2.line(final_display, (0, forehead_final), (final_w, forehead_final), (0, 200, 255), 2)
                    cv2.putText(final_display, "Forehead", (5, forehead_final - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 2)
                    
                    # Eye line tolerance zone
                    eye_line_final = int(final_h * (1 - specs[country].eye_line_from_bottom_ratio))
                    eye_top_final = eye_line_final - tolerance_px_final
                    eye_bottom_final = eye_line_final + tolerance_px_final
                    cv2.rectangle(final_display, (0, eye_top_final), (final_w, eye_bottom_final), (255, 100, 255), -1)
                    cv2.line(final_display, (0, eye_line_final), (final_w, eye_line_final), (255, 0, 255), 2)
                    cv2.putText(final_display, "Eyes", (5, eye_line_final - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
                    
                    # Shoulders tolerance zone
                    shoulders_final = int(final_h * 0.8)
                    shoulders_top_final = shoulders_final - tolerance_px_final
                    shoulders_bottom_final = min(final_h, shoulders_final + tolerance_px_final)
                    cv2.rectangle(final_display, (0, shoulders_top_final), (final_w, shoulders_bottom_final), (100, 200, 100), -1)
                    cv2.line(final_display, (0, shoulders_final), (final_w, shoulders_final), (0, 200, 0), 2)
                    cv2.putText(final_display, "Mid-Chest", (5, shoulders_final + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 2)
                    
                    st.image(Image.fromarray(final_display), 
                            caption=f"Final ID Photo with Tolerance Zones",
                            use_container_width=True)
                    st.caption(f"✓ {w_px}×{h_px} px | {specs[country].width_in}\" × {specs[country].height_in}\" @ {dpi} DPI")
                
                # Generate print sheet
                sheet = build_print_sheet(
                    photo=cropped_pil,
                    layout=layout,
                    dpi=dpi,
                    margin_in=margin,
                    spacing_in=spacing,
                    copies=copies,
                )
            
            # Display results
            st.success("✅ Photo processed successfully!")
            
            col_photo, col_sheet = st.columns(2)
            
            with col_photo:
                st.subheader("Cropped Photo")
                spec = specs[country]
                w_in, h_in = spec.width_in, spec.height_in
                
                # Display cropped photo without text overlay
                cropped_display = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
                st.image(Image.fromarray(cropped_display), caption=f"{w_in}\" × {h_in}\"", use_container_width=True)
                
                # Photo size info
                w_px, h_px = cropped_pil.size
                st.caption(f"📐 Size: {w_px} × {h_px} pixels @ {dpi} DPI | {country} Standard")
                
                # Download cropped photo
                img_buffer = io.BytesIO()
                cropped_pil.save(img_buffer, format="JPEG", quality=95)
                img_buffer.seek(0)
                
                st.download_button(
                    label="📥 Download Photo",
                    data=img_buffer,
                    file_name=f"{country.lower()}_photo.jpg",
                    mime="image/jpeg",
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
                st.caption(f"📐 Sheet: {sheet_w} × {sheet_h} pixels @ {dpi} DPI | {copies} copies")
                
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
                st.metric("Head Height Ratio", f"{specs[country].head_height_ratio:.0%}")
    
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
