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

st.title("📸 ID Photo Processor")
st.markdown("Auto-crop and process identity photos for passport compliance")

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
    st.header("Settings")
    
    # Country selection
    country = st.selectbox(
        "Select Country",
        options=list(specs.keys()),
        format_func=lambda x: f"{x} - {specs[x].name}",
        help="Choose the country specification for your ID photo"
    )
    
    # Photo settings
    st.subheader("Photo Settings")
    replace_bg = st.checkbox("Replace Background", value=False)
    dpi = st.slider("DPI (Quality)", min_value=100, max_value=600, value=300, step=50)
    
    # Layout settings
    st.subheader("Print Layout")
    layout_preset = st.radio("Layout Size", ["4x6", "6x6", "Custom"])
    
    if layout_preset == "Custom":
        layout_w = st.number_input("Width (inches)", value=4.0, min_value=1.0, step=0.5)
        layout_h = st.number_input("Height (inches)", value=6.0, min_value=1.0, step=0.5)
        layout = LayoutSpec(width_in=layout_w, height_in=layout_h)
    else:
        layout = parse_layout(layout_preset)
    
    copies = st.slider("Number of Copies", min_value=1, max_value=20, value=6)
    margin = st.number_input("Margin (inches)", value=0.1, min_value=0.0, step=0.05)
    spacing = st.number_input("Spacing (inches)", value=0.1, min_value=0.0, step=0.05)

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload Photo")
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=["jpg", "jpeg", "png"],
        help="Upload a clear, front-facing photo"
    )

with col2:
    st.subheader("Photo Info")
    if uploaded_file:
        st.info(f"📁 File: {uploaded_file.name}")
        st.info(f"📏 Size: {uploaded_file.size:,} bytes")

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
            processing_mode = st.radio(
                "Processing Mode",
                ["Automatic", "Manual Adjustment"],
                horizontal=True,
                help="Automatic: AI detects face. Manual: You adjust the crop area."
            )
            
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
                st.subheader("📐 Manual Crop Adjustment - Head & Shoulder Profile")
                st.markdown("""
                **Objective**: Adjust the green crop box to frame head and shoulders correctly.  
                Use the sliders below to position the crop area precisely.
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
                st.markdown("### 🔍 Zoom Control (50% = Zoom Out, 200% = Zoom In)")
                col_zoom1, col_zoom2, col_zoom3 = st.columns([2, 1, 1])
                with col_zoom1:
                    zoom_level = st.slider(
                        "Zoom Level",
                        min_value=50, max_value=200, value=100, step=5,
                        key="zoom_slider",
                        help="Zoom percentage: 50% = zoomed out, 200% = zoomed in"
                    )
                with col_zoom2:
                    st.metric("Current Zoom", f"{zoom_level}%")
                with col_zoom3:
                    st.info(f"📏 {zoom_level/100:.1f}x")
                
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
                
                st.markdown("### 🎯 Adjust Crop Boundaries")
                st.markdown("*Use sliders OR +/- buttons to position the crop frame around the head and shoulders*")
                
                # Scale buttons (+ to enlarge crop area, - to shrink)
                st.markdown("**🔄 Scale Crop Area:**")
                col_scale1, col_scale2, col_scale3, col_scale4, col_scale5 = st.columns(5)
                with col_scale1:
                    if st.button("➖ Shrink", key="shrink_crop", help="Shrink the crop area by 5%"):
                        st.session_state.scale_factor = getattr(st.session_state, 'scale_factor', 1.0) - 0.05
                with col_scale2:
                    scale_display = getattr(st.session_state, 'scale_factor', 1.0)
                    st.metric("Scale", f"{scale_display:.0%}")
                with col_scale3:
                    if st.button("➕ Enlarge", key="enlarge_crop", help="Enlarge the crop area by 5%"):
                        st.session_state.scale_factor = getattr(st.session_state, 'scale_factor', 1.0) + 0.05
                with col_scale4:
                    if st.button("🔄 Reset", key="reset_crop", help="Reset to default size"):
                        st.session_state.scale_factor = 1.0
                with col_scale5:
                    st.write("")  # Spacer
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    crop_top_pct = st.slider(
                        "Top %",
                        0, 50, default_top, 1,
                        key="manual_crop_top",
                        help="% from top of image"
                    )
                with col2:
                    crop_bottom_pct = st.slider(
                        "Bottom %",
                        crop_top_pct + 30, 100, default_bottom, 1,
                        key="manual_crop_bottom",
                        help="% from top of image"
                    )
                with col3:
                    crop_left_pct = st.slider(
                        "Left %",
                        0, 40, default_left, 1,
                        key="manual_crop_left",
                        help="% from left of image"
                    )
                with col4:
                    crop_right_pct = st.slider(
                        "Right %",
                        crop_left_pct + 40, 100, default_right, 1,
                        key="manual_crop_right",
                        help="% from left of image"
                    )
                
                # Apply scale factor from +/- buttons
                scale_factor = getattr(st.session_state, 'scale_factor', 1.0)
                scale_factor = max(0.5, min(2.0, scale_factor))  # Clamp between 0.5x and 2.0x
                
                # Calculate scaled crop boundaries
                # Center the crop area and scale it
                center_y = (crop_top_pct + crop_bottom_pct) / 2
                center_x = (crop_left_pct + crop_right_pct) / 2
                
                height_range = crop_bottom_pct - crop_top_pct
                width_range = crop_right_pct - crop_left_pct
                
                # Apply scale factor
                scaled_height = height_range * scale_factor
                scaled_width = width_range * scale_factor
                
                # Keep within bounds
                crop_top_pct_scaled = max(0, min(50, center_y - scaled_height / 2))
                crop_bottom_pct_scaled = min(100, max(crop_top_pct_scaled + 30, center_y + scaled_height / 2))
                crop_left_pct_scaled = max(0, min(40, center_x - scaled_width / 2))
                crop_right_pct_scaled = min(100, max(crop_left_pct_scaled + 40, center_x + scaled_width / 2))
                
                # Apply manual crop on zoomed image with scaled boundaries
                y1 = int(h_zoom * crop_top_pct_scaled / 100)
                y2 = int(h_zoom * crop_bottom_pct_scaled / 100)
                x1 = int(w_zoom * crop_left_pct_scaled / 100)
                x2 = int(w_zoom * crop_right_pct_scaled / 100)
                
                manual_cropped_bgr = image_zoomed[y1:y2, x1:x2]
                
                # Resize to spec dimensions
                spec = specs[country]
                w_px, h_px = int(round(spec.width_in * dpi)), int(round(spec.height_in * dpi))
                manual_cropped_bgr = cv2.resize(manual_cropped_bgr, (w_px, h_px), interpolation=cv2.INTER_CUBIC)
                
                manual_cropped_rgb = cv2.cvtColor(manual_cropped_bgr, cv2.COLOR_BGR2RGB)
                cropped_pil = Image.fromarray(manual_cropped_rgb)
                
                # Show live preview with crop box overlay
                st.markdown("### 📸 Live Preview")
                st.markdown("*Green box shows the area that will be cropped and used as your ID photo*")
                
                col_preview1, col_preview2 = st.columns(2)
                with col_preview1:
                    # Draw rectangle showing crop area on zoomed image
                    img_display = image_zoomed.copy()
                    
                    # Draw outer rectangle with thick green border
                    cv2.rectangle(img_display, (x1, y1), (x2, y2), (0, 255, 0), 4)
                    
                    # Add crosshair at center
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    line_len = 30
                    cv2.line(img_display, (center_x - line_len, center_y), (center_x + line_len, center_y), (0, 255, 0), 2)
                    cv2.line(img_display, (center_x, center_y - line_len), (center_x, center_y + line_len), (0, 255, 0), 2)
                    
                    # Add corner markers
                    corner_size = 20
                    cv2.line(img_display, (x1, y1), (x1 + corner_size, y1), (0, 200, 255), 3)
                    cv2.line(img_display, (x1, y1), (x1, y1 + corner_size), (0, 200, 255), 3)
                    
                    # Add crop dimensions overlay on image
                    crop_w = x2 - x1
                    crop_h = y2 - y1
                    dim_text = f"CROP: {crop_w}×{crop_h} px (Zoom: {zoom_level}%, Scale: {scale_factor:.0%})"
                    cv2.putText(img_display, dim_text, (x1 + 10, y1 - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    img_display_rgb = cv2.cvtColor(img_display, cv2.COLOR_BGR2RGB)
                    st.image(Image.fromarray(img_display_rgb), 
                            caption=f"Original Image - Crop Region Highlighted (Green Box)",
                            use_container_width=True)
                    
                    # Show crop dimensions
                    st.caption(f"📐 Crop region: {crop_w}×{crop_h} px | {crop_top_pct}-{crop_bottom_pct}% height, {crop_left_pct}-{crop_right_pct}% width")
                
                with col_preview2:
                    # Add dimensions overlay on final photo
                    final_photo_display = cv2.cvtColor(cropped_bgr.copy(), cv2.COLOR_BGR2RGB)
                    final_photo_pil = Image.fromarray(final_photo_display)
                    
                    # Draw semi-transparent background for text
                    final_photo_cv = cropped_bgr.copy()
                    h_photo, w_photo = final_photo_cv.shape[:2]
                    
                    # Draw dimension text at top
                    dim_text = f"SIZE: {w_px} × {h_px} px | {specs[country].width_in}\" × {specs[country].height_in}\" @ {dpi} DPI"
                    text_size = cv2.getTextSize(dim_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    cv2.rectangle(final_photo_cv, (10, 5), (10 + text_size[0] + 10, 30), (0, 0, 0), -1)
                    cv2.putText(final_photo_cv, dim_text, (15, 25), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    final_photo_display_rgb = cv2.cvtColor(final_photo_cv, cv2.COLOR_BGR2RGB)
                    st.image(Image.fromarray(final_photo_display_rgb), 
                            caption=f"Final ID Photo",
                            use_container_width=True)
                    st.caption(f"✓ This is your final cropped and resized photo")
                
                cropped_bgr = manual_cropped_bgr
                
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
                
                # Add dimensions overlay to cropped photo
                cropped_with_dims = cv2.cvtColor(cropped_bgr.copy(), cv2.COLOR_BGR2RGB)
                h_final, w_final = cropped_bgr.shape[:2]
                
                # Draw dimension text with background
                dim_text = f"{w_final} × {h_final} px | {w_in}\" × {h_in}\" | {dpi} DPI"
                text_size = cv2.getTextSize(dim_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                cv2.rectangle(cropped_with_dims, (10, 5), (10 + text_size[0] + 10, 35), (0, 0, 0), -1)
                cv2.putText(cropped_with_dims, dim_text, (15, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Also add country specification at bottom
                spec_text = f"{country} Standard"
                spec_size = cv2.getTextSize(spec_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(cropped_with_dims, (10, h_final - 35), (10 + spec_size[0] + 10, h_final - 5), (0, 0, 0), -1)
                cv2.putText(cropped_with_dims, spec_text, (15, h_final - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
                
                st.image(Image.fromarray(cropped_with_dims), caption=f"{w_in}\" × {h_in}\"", use_container_width=True)
                
                # Photo size info
                w_px, h_px = cropped_pil.size
                st.caption(f"📐 Size: {w_px} × {h_px} pixels @ {dpi} DPI")
                
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
                
                # Add dimensions overlay to print sheet
                sheet_with_dims = sheet.copy()
                sheet_cv = cv2.cvtColor(np.array(sheet_with_dims), cv2.COLOR_RGB2BGR)
                sheet_h, sheet_w = sheet_cv.shape[:2]
                
                # Draw print sheet information
                info_text = f"Sheet: {sheet_w} × {sheet_h} px | {layout.width_in}\" × {layout.height_in}\" | {copies} copies @ {dpi} DPI"
                text_size = cv2.getTextSize(info_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                cv2.rectangle(sheet_cv, (10, 5), (10 + text_size[0] + 10, 35), (0, 0, 0), -1)
                cv2.putText(sheet_cv, info_text, (15, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Add layout type at bottom
                layout_text = f"Layout: {int(layout.width_in)}\" × {int(layout.height_in)}\""
                layout_size = cv2.getTextSize(layout_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(sheet_cv, (10, sheet_h - 35), (10 + layout_size[0] + 10, sheet_h - 5), (0, 0, 0), -1)
                cv2.putText(sheet_cv, layout_text, (15, sheet_h - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
                
                sheet_cv_rgb = cv2.cvtColor(sheet_cv, cv2.COLOR_BGR2RGB)
                st.image(Image.fromarray(sheet_cv_rgb), caption=f"Print Layout: {layout.width_in}\" × {layout.height_in}\"", use_container_width=True)
                
                # Sheet size info
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
