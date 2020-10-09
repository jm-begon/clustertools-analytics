from collections import defaultdict

from clustertools_analytics.array.base import CellType, Row, Table


class CellCustomizer(object):
    @classmethod
    def get_default_filter_class(cls):
        return CellType

    def approve(self, cell):
        return isinstance(cell, self.__class__.get_default_filter_class())

    def memo_if_approved(self, cell):
        if self.approve(cell):
            self.memo(cell)

    def memo(self, cell_value):
        pass

    def pack(self):
        pass


    def customize_approved_cell(self, cell):
        pass

    def __call__(self, cell):
        if self.approve(cell):
            self.customize_approved_cell(cell)


class ContentIterator(object):
    def __init__(self, table, filter_class=CellType):
        self.table = table
        self.filter_class = filter_class
        self.row_slice = slice(None)
        self.col_slice = slice(None)

    def __getitem__(self, item):
        if isinstance(item, slice):
            self.row_slice = item
        else:
            self.row_slice, self.col_slice = item

    def __iter__(self):
        content = [r for r in self.table.rows if isinstance(r, Row)]
        content = content[self.row_slice]
        content = [row[self.col_slice] for row in content]
        for r, row in enumerate(content):
            for c, cell in enumerate(row):
                if isinstance(cell, self.filter_class):
                    yield r, c, cell



class TableCustomizer(object):
    def first_pass(self, row, col, cell):
        pass

    def customize_cell(self, row, col, cell):
        pass

    def pack(self):
        pass

    def __call__(self, content_iterator):
        if isinstance(content_iterator, Table):
            content_iterator = ContentIterator(content_iterator)

        for r, c, cell in content_iterator:
            self.first_pass(r, c, cell)

        self.pack()

        for r, c, cell in content_iterator:
            self.customize_cell(r, c, cell)



class TableSubsetCustomizer(TableCustomizer):
    def __init__(self, cell_customizer_factory):
        self.cell_customizers = defaultdict(cell_customizer_factory)

    def _get_cell_customizer(self, row, column):
        return self.cell_customizers[0]

    def first_pass(self, row, col, cell):
        cell_customizer = self._get_cell_customizer(row, col)
        cell_customizer.memo_if_approved(cell)

    def customize_cell(self, row, col, cell):
        cell_customizer = self._get_cell_customizer(row, col)
        cell_customizer(cell)

    def pack(self):
        for customizer in self.cell_customizers.values():
            customizer.pack()



class ColumnColorFormater(TableSubsetCustomizer):
    def _get_cell_customizer(self, row, column):
        return self.cell_customizers[column]


class RowColorFormater(TableSubsetCustomizer):
    def _get_cell_customizer(self, row, column):
        return self.cell_customizers[row]