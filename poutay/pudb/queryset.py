from datetime import datetime
from typing import List, Optional, Tuple, Union

class QuerySet:
    def __init__(
        self,
        model_cls,
        filters: Optional[dict] = None,
        date_range: Optional[Tuple[str, str]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None
    ):
        self.model_cls = model_cls
        self.filters = filters or {}
        self.date_range = date_range
        self.order = order
        self.limit = limit
        self._result_cache = None

    def fetch(self):
        if self._result_cache is not None:
            return

        if self.limit == 1:
            # فقط یک نتیجه می‌خوایم، می‌تونیم از ایندکس استفاده کنیم
            result = self.model_cls._search_with_index(self.filters, self.date_range, limit=1)
            self._result_cache = result
        else:
            results = self.model_cls._search_with_index(self.filters, self.date_range)
            if self.order:
                reverse = False
                field = self.order
                if field.startswith("-"):
                    reverse = True
                    field = field[1:]
                results.sort(key=lambda x: getattr(x, field, None), reverse=reverse)

            self._result_cache = results

    def __len__(self):
        self.fetch()
        return len(self._result_cache)

    def __iter__(self):
        self.fetch()
        return iter(self._result_cache)

    def __getitem__(self, item: Union[int, slice]):
        self.fetch()
        return self._result_cache[item]

    def filter(self, **kwargs):
        combined = self.filters.copy()
        combined.update(kwargs)
        return QuerySet(
            self.model_cls,
            combined,
            self.date_range,
            self.order,
            self.limit
        )

    def between(self, start_date: str, end_date: str):
        return QuerySet(
            self.model_cls,
            self.filters,
            (start_date, end_date),
            self.order,
            self.limit
        )

    def order_by(self, field_name: str):
        return QuerySet(
            self.model_cls,
            self.filters,
            self.date_range,
            order=field_name,
            limit=self.limit
        )

    def all(self) -> List:
        # self.fetch()
        return self

    def first(self):
        if self._result_cache is None:
            # اگر هنوز cache نیست، فقط یکی بخون
            result = self.model_cls._search_with_index(self.filters, self.date_range, limit=1)
            self._result_cache = result
        return self._result_cache[0] if self._result_cache else None

    def paginate(self, page=1, per_page=10):
        self.fetch()
        start = (page - 1) * per_page
        end = start + per_page
        return self._result_cache[start:end]
