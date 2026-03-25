def create_box(doc, name, width, depth, height, x=0, y=0, z=0):
    import FreeCAD as App
    import Part

    shape = Part.makeBox(width, depth, height)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    obj.Placement.Base = App.Vector(x, y, z)
    return obj


def create_rect_prism(doc, name, width, depth, height, x, y, z=0):
    return create_box(doc, name, width, depth, height, x=x, y=y, z=z)


def create_surface_prism(doc, name, surface, height, x=0, y=0, z=0):
    shape_type = surface.shape
    if shape_type == "rectangle":
        return create_box(doc, name, surface.width, surface.height, height, x=x, y=y, z=z)
    if shape_type == "rounded_rect":
        return create_rounded_rect_prism(
            doc,
            name,
            width=surface.width,
            depth=surface.height,
            height=height,
            corner_radius=surface.corner_radius or 0.0,
            x=x,
            y=y,
            z=z,
        )
    if shape_type == "polygon":
        return create_polygon_prism(
            doc,
            name,
            points=surface.points or (),
            height=height,
            x=x,
            y=y,
            z=z,
        )
    raise ValueError(f"Unsupported controller surface shape: {shape_type}")


def create_rounded_rect_prism(doc, name, width, depth, height, corner_radius, x=0, y=0, z=0):
    import FreeCAD as App
    import Part

    base = Part.makeBox(width, depth, height)
    radius = min(float(corner_radius), width / 2.0, depth / 2.0)
    if radius > 0:
        vertical_edges = [
            edge
            for edge in base.Edges
            if hasattr(edge, "BoundBox") and abs(edge.BoundBox.ZLength - height) < 1e-6
        ]
        if vertical_edges:
            base = base.makeFillet(radius, vertical_edges)

    obj = doc.addObject("Part::Feature", name)
    obj.Shape = base
    obj.Placement.Base = App.Vector(x, y, z)
    return obj


def create_polygon_prism(doc, name, points, height, x=0, y=0, z=0):
    import FreeCAD as App
    import Part

    if len(points) < 3:
        raise ValueError("Polygon surface requires at least three points")

    vectors = [App.Vector(px, py, 0) for px, py in points]
    if vectors[0] != vectors[-1]:
        vectors.append(vectors[0])
    wire = Part.makePolygon(vectors)
    face = Part.Face(wire)
    prism = face.extrude(App.Vector(0, 0, height))

    obj = doc.addObject("Part::Feature", name)
    obj.Shape = prism
    obj.Placement.Base = App.Vector(x, y, z)
    return obj


def create_cylinder(doc, name, radius, height, x, y, z=0):
    import FreeCAD as App
    import Part

    cylinder = Part.makeCylinder(radius, height)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = cylinder
    obj.Placement.Base = App.Vector(x, y, z)
    return obj


def cut(base_obj, tool_obj, name=None):
    result = base_obj.Shape.cut(tool_obj.Shape)
    obj = base_obj.Document.addObject(
        "Part::Feature",
        name or f"{base_obj.Name}_cut",
    )
    obj.Shape = result
    return obj
