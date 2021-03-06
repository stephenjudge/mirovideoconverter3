import itertools

from AppKit import *

from .base import Widget

def _extra_space_iter(extra_length, count):
    """Utility function to allocate extra space left over in containers."""
    if count == 0:
        return
    extra_space, leftover = divmod(extra_length, count)
    while leftover >= 1:
        yield extra_space + 1
        leftover -= 1
    yield extra_space + leftover
    while True:
        yield extra_space


class BoxPacking:
    """Utility class to store how we are packing a single widget."""

    def __init__(self, widget, expand, padding):
        self.widget = widget
        self.expand = expand
        self.padding = padding


class Box(Widget):
    """Base class for HBox and VBox.  """
    CREATES_VIEW = False

    def __init__(self, spacing=0):
        super(Box, self).__init__()
        self.spacing = spacing
        self.packing_start = []
        self.packing_end = []
        self.expand_count = 0

    def packing_both(self):
        return itertools.chain(self.packing_start, self.packing_end)

    def get_children(self):
        for packing in self.packing_both():
            yield packing.widget
    children = property(get_children)

    # Internally Boxes use a (length, breadth) coordinate system.  length and
    # breadth will be either x or y depending on which way the box is
    # oriented.  The subclasses must provide methods to translate between the
    # 2 coordinate systems.

    def translate_size(self, size):
        """Translate a (width, height) tulple to (length, breadth)."""
        raise NotImplementedError()

    def untranslate_size(self, size):
        """Reverse the work of translate_size."""
        raise NotImplementedError()

    def make_child_rect(self, position, length):
        """Create a rect to position a child with."""
        raise NotImplementedError()

    def pack_start(self, child, expand=False, padding=0):
        self.packing_start.append(BoxPacking(child, expand, padding))
        if expand:
            self.expand_count += 1

    def pack_end(self, child, expand=False, padding=0):
        self.packing_end.append(BoxPacking(child, expand, padding))
        if expand:
            self.expand_count += 1

    def _remove_from_packing(self, child):
        for i in xrange(len(self.packing_start)):
            if self.packing_start[i].widget is child:
                return self.packing_start.pop(i)
        for i in xrange(len(self.packing_end)):
            if self.packing_end[i].widget is child:
                return self.packing_end.pop(i)
        raise LookupError("%s not found" % child)

    def remove(self, child):
        packing = self._remove_from_packing(child)
        if packing.expand:
            self.expand_count -= 1

    def translate_widget_size(self, widget):
        return self.translate_size(widget.get_size_request())

    def calc_size_request(self):
        length = breadth = 0
        for packing in self.packing_both():
            child_length, child_breadth = \
                    self.translate_widget_size(packing.widget)
            length += child_length
            if packing.padding:
                length += packing.padding * 2 # Need to pad on both sides
            breadth = max(breadth, child_breadth)
        spaces = max(0, len(self.packing_start) + len(self.packing_end) - 1)
        length += spaces * self.spacing
        return self.untranslate_size((length, breadth))

    def place_children(self):
        request_length, request_breadth = self.translate_widget_size(self)
        ps = self.viewport.placement.size
        total_length, dummy = self.translate_size((ps.width, ps.height))
        total_extra_space = total_length - request_length
        extra_space_iter = _extra_space_iter(total_extra_space,
                self.expand_count)
        start_end = self._place_packing_list(self.packing_start, 
                extra_space_iter, 0)
        if self.expand_count == 0 and total_extra_space > 0:
            # account for empty space after the end of pack_start list and
            # before the pack_end list.
            self.draw_empty_space(start_end, total_extra_space)
            start_end += total_extra_space
        self._place_packing_list(reversed(self.packing_end), extra_space_iter, 
                start_end)

    def draw_empty_space(self, start, length):
        empty_rect = self.make_child_rect(start, length)
        my_view = self.viewport.view
        opaque_view = my_view.opaqueAncestor()
        if opaque_view is not None:
            empty_rect2 = opaque_view.convertRect_fromView_(empty_rect, my_view)
            opaque_view.setNeedsDisplayInRect_(empty_rect2)

    def _place_packing_list(self, packing_list, extra_space_iter, position):
        for packing in packing_list:
            child_length, child_breadth = \
                    self.translate_widget_size(packing.widget)
            if packing.expand:
                child_length += extra_space_iter.next()
            if packing.padding: # space before
                self.draw_empty_space(position, packing.padding)
                position += packing.padding
            child_rect = self.make_child_rect(position, child_length)
            if packing.padding: # space after
                self.draw_empty_space(position, packing.padding)
                position += packing.padding
            packing.widget.place(child_rect, self.viewport.view)
            position += child_length
            if self.spacing > 0:
                self.draw_empty_space(position, self.spacing)
                position += self.spacing
        return position

    def viewport_created(self):
        self.place_children()

    def viewport_repositioned(self):
        self.place_children()

class VBox(Box):

    def translate_size(self, size):
        return (size[1], size[0])

    def untranslate_size(self, size):
        return (size[1], size[0])

    def make_child_rect(self, position, length):
        placement = self.viewport.placement
        return NSMakeRect(placement.origin.x, placement.origin.y + position,
                placement.size.width, length)


class HBox(Box):

    def translate_size(self, size):
        return (size[0], size[1])

    def untranslate_size(self, size):
        return (size[0], size[1])

    def make_child_rect(self, position, length):
        placement = self.viewport.placement
        return NSMakeRect(placement.origin.x + position, placement.origin.y,
                length, placement.size.height)
