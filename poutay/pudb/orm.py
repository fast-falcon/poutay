import json
import os
from datetime import datetime
from typing import Optional
import uuid
from .auth import AuthManager
import re

from .encryption import get_fernet_key
from .queryset import QuerySet
from .tree_index import TreeNode


class Field:
    def __init__(self, label=None, default=None):
        self.label = label
        self.default = default


class RelatedField:
    def __init__(self, to_model, related_name=None):
        self.to_model = to_model
        self.related_name = related_name


class ForeignKey(RelatedField):
    pass


class OneToOne(RelatedField):
    pass


class ManyToManyField:
    def __init__(self, to_model, related_name=None):
        self.to_model = to_model
        self.related_name = related_name
        self.through = None  # auto-generated later


class BaseModelMeta(type):
    def __new__(cls, m_name, bases, attrs):
        fields = {k: v for k, v in attrs.items() if isinstance(v, (Field,RelatedField))}
        if "id" not in fields:
            fields.update({"id": Field("id")})
        attrs['_declared_fields'] = fields

        relations = {k: v for k, v in attrs.items() if isinstance(v, RelatedField)}
        attrs['_declared_relations'] = relations
        attrs['_declared_m2m_fields'] = [
            k for k, v in attrs.items() if isinstance(v, ManyToManyField)
        ]
        for rel_name, rel in relations.items():
            if rel.related_name:
                related_model = rel.to_model
                # ثبت در لیست مربوطه
                if not hasattr(related_model, "_reverse_relations"):
                    related_model._reverse_relations = {}
                related_model._reverse_relations.setdefault(rel.related_name, []).append((m_name, rel_name, type(rel)))
        new_cls = super().__new__(cls, m_name, bases, attrs)
        for name, field in attrs.items():
            if isinstance(field, ManyToManyField):
                to_model = field.to_model
                model_name = f"{name}_{uuid.uuid4().hex[:8]}"  # unique name

                # ساخت مدل میانی (درون‌ساز)
                through_attrs = {
                    '__module__': attrs.get('__module__', '__main__'),
                    'from_model': ForeignKey(None),
                    'to_model': ForeignKey(to_model),
                    'id': Field()
                }

                # اتصال مدل جاری بعداً انجام می‌شود
                through_model = type(f"{name.capitalize()}Through", (new_cls.base_model,), through_attrs)
                field.through = through_model
                attrs[name] = field  # نگه‌داری در کلاس اصلی

                # ثبت در مدل مقصد برای reverse
                if field.related_name:
                    if not hasattr(to_model, "_reverse_m2m"):
                        to_model._reverse_m2m = {}
                    to_model._reverse_m2m[field.related_name] = {
                        "through": through_model,
                        "from_field": "to_model",
                        "to_model": new_cls,  # بعداً ست میشه
                        "to_field": "from_model"
                    }
        for name, field in attrs.items():
            if isinstance(field, ManyToManyField):
                field.through._declared_relations['from_model'].to_model = new_cls
        if new_cls.base_model:
            if not hasattr(new_cls.base_model, '_registry'):
                new_cls.base_model._registry = {}
            new_cls.base_model._registry[m_name] = new_cls
        return new_cls


class M2MQuerySetWrapper:
    def __init__(self, instance, through, to_model, from_field, to_field):
        self.instance = instance
        self.through = through
        self.to_model = to_model
        self.from_field = from_field
        self.to_field = to_field
        self._queryset = None

    def _fetch_queryset(self):
        if self._queryset is None:
            # گرفتن رکوردهای پیوند خورده از جدول میانی
            links = self.through.objects().filter(**{
                self.from_field: self.instance.id
            }).all()
            ids = [getattr(link, self.to_field) for link in links]
            self._queryset = self.to_model.objects().filter(id__in=ids)
        return self._queryset

    def add(self, *objs):
        for obj in objs:
            # جلوگیری از دوباره اضافه شدن
            existing = self.through.objects().filter(
                **{
                    self.from_field: self.instance.id,
                    self.to_field: obj.id
                }
            ).first()
            if not existing:
                link = self.through(**{
                    self.from_field: self.instance.id,
                    self.to_field: obj.id
                })
                link.save()
        self._queryset = None  # کش را پاک کن

    def remove(self, obj):
        self.through.delete(**{
            self.from_field: self.instance.id,
            self.to_field: obj.id
        })
        self._queryset = None

    def clear(self):
        self.through.delete(**{
            self.from_field: self.instance.id
        })
        self._queryset = None

    def all(self):
        return self._fetch_queryset()

    def __iter__(self):
        return iter(self._fetch_queryset())

    def __getitem__(self, item):
        return self._fetch_queryset()[item]

    def __len__(self):
        return len(self._fetch_queryset())

    def __getattr__(self, item):
        return getattr(self._fetch_queryset(), item)


class BaseModel(metaclass=BaseModelMeta):
    base_model = None
    _auth = None
    _password = None
    _db_root = 'mydb'
    _indexes = {}
    _cache_loaded_dates = set()

    def __init__(self, **kwargs):
        if "id" in self._declared_fields and "id" not in kwargs:
            kwargs["id"] = str(uuid.uuid4())

        for field in self._declared_fields:
            setattr(self, field, kwargs.get(field))
        for rel_field in self._declared_relations:
            value = kwargs.get(rel_field)
            setattr(self, f"_{rel_field}_id", value)  # فقط id ذخیره می‌کنیم
            setattr(self, f"_{rel_field}_cache", None)
        for m2m_field in getattr(self.__class__, '_declared_m2m_fields', []):
            setattr(self, f"_{m2m_field}_ids", [])

    def __getattribute__(self, name):
        # اول تلاش کن از حالت عادی مقدار بگیری
        # try:
        #     return super().__getattribute__(name)
        # except AttributeError:
        #     pass

        # حالا چک کنیم آیا این name یک فیلد ManyToMany هست؟
        cls = type(self)
        if name in getattr(cls, '_declared_m2m_fields', []):
            field = getattr(cls, name)



            return M2MQuerySetWrapper(
                instance=self,
                through=field.through,
                to_model=field.to_model,
                from_field="from_model",
                to_field="to_model"
            )
        else:
            return super().__getattribute__(name)
        # اگر هیچ چیز پیدا نشد
        raise AttributeError(f"{name} not found in {cls.__name__}")

    def __getattr__(self, name):
        if name in self._declared_relations:
            rel_field = self._declared_relations[name]
            rel_id = getattr(self, f"_{name}_id", None)
            cache = getattr(self, f"_{name}_cache", None)

            if cache:
                return cache
            if rel_id is None:
                return None

            model_cls = rel_field.to_model
            if isinstance(rel_id, list):
                # ManyToMany
                related_objs = model_cls.objects().filter(id__in=rel_id).all()
                setattr(self, f"_{name}_cache", related_objs)
                return related_objs
            else:
                # FK یا OneToOne
                related_obj = model_cls.objects().filter(id=rel_id).first()
                setattr(self, f"_{name}_cache", related_obj)
                return related_obj
        if hasattr(self.__class__, '_reverse_m2m'):
            m2m_map = self.__class__._reverse_m2m
            if name in m2m_map:
                conf = m2m_map[name]
                through = conf["through"]
                from_field = conf["from_field"]
                to_model = conf["to_model"] or None  # در صورت نیاز قابل تنظیم

                links = through.objects().filter(**{from_field: self.id}).all()
                ids = [link.from_model for link in links]
                return conf["to_model"].objects().filter(id__in=ids)
        if hasattr(self.__class__, "_reverse_relations"):
            reverse_map = self.__class__._reverse_relations
            if name in reverse_map:
                for model_name, field_name, rel_type in reverse_map[name]:
                    model_cls = self.base_model._registry[model_name]
                    filter_kwargs = {field_name: self.id}
                    qs = model_cls.objects().filter(**filter_kwargs)
                    if rel_type is OneToOne:
                        return qs.first()
                    return qs  # ForeignKey → QuerySet (قابل پیمایش)
        if hasattr(self.__class__, '_declared_m2m_fields') and name in self.__class__._declared_m2m_fields:
            field = getattr(self.__class__, name)
            through = field.through
            to_model = field.to_model

            class M2MManager:
                def __init__(self, instance):
                    self.instance = instance

                def add(self, *objs):
                    for obj in objs:
                        through_obj = through(
                            from_model=self.instance.id,
                            to_model=obj.id
                        )
                        through_obj.save()

                def all(self):
                    links = through.objects().filter(from_model=self.instance.id).all()
                    ids = [link.to_model for link in links]
                    return to_model.objects().filter(id__in=ids)

                def remove(self, obj):
                    through_cls = field.through
                    through_cls.delete(from_model=self.instance.id, to_model=obj.id)

            return M2MManager(self)
        raise AttributeError(f"{name} not found in {self.__class__.__name__}")

    def to_dict(self):
        data = {}
        for f in self._declared_fields :
            val = getattr(self, f)
            if not val:
                val = getattr(self._declared_fields[f], "default")
            data[f] = val
        # data = {f: getattr(self, f) for f in self._declared_fields}
        for rel in self._declared_relations:
            rel_id = getattr(self, f"_{rel}_id", None)
            data[rel] = rel_id
        return data

    @classmethod
    def from_dict(cls, data):
        kwargs = {}
        for f in cls._declared_fields:
            kwargs[f] = data.get(f)
        for r in cls._declared_relations:
            kwargs[r] = data.get(r)
        return cls(**kwargs)

    @classmethod
    def objects(cls):
        return QuerySet(cls)

    @classmethod
    def _get_file_path(cls, date_str):
        y, m, d = date_str.split("-")
        path = os.path.join(cls._db_root, y, m, d)
        os.makedirs(path, exist_ok=True)
        return os.path.join(path, f"{cls.__name__}.pu")

    def save(self):
        if not self.__class__._auth or not self.__class__._auth.is_authenticated():
            raise PermissionError("Login required")

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        file_path = self._get_file_path(date_str)
        fernet = get_fernet_key(self.__class__._password)
        data = []

        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                try:
                    decrypted = fernet.decrypt(f.read())
                    data = json.loads(decrypted.decode())
                except:
                    pass

        record = self.to_dict()
        data.append(record)

        with open(file_path, 'wb') as f:
            f.write(fernet.encrypt(json.dumps(data).encode()))

        self._update_index(record, date_str)

    @classmethod
    def _update_index(cls, item, date_str):
        clsname = cls.__name__
        if clsname not in cls._indexes:
            cls._indexes[clsname] = {f: TreeNode() for f in cls._declared_fields}
        for field, value in item.items():
            cls._indexes[clsname][field].insert([str(value)], item)
        cls._cache_loaded_dates.add(date_str)

    @classmethod
    def _build_index(cls, date_range=None):
        clsname = cls.__name__
        if clsname not in cls._indexes:
            cls._indexes[clsname] = {f: TreeNode() for f in cls._declared_fields}
        fernet = get_fernet_key(cls._password)

        for root, _, files in os.walk(cls._db_root):
            for file in files:
                if not file.endswith('.pu') or not file.startswith(clsname):
                    continue
                parts = root.split(os.sep)[-3:]
                date_str = "-".join(parts)
                if date_range:
                    start, end = map(lambda d: datetime.strptime(d, "%Y-%m-%d"), date_range)
                    current = datetime.strptime(date_str, "%Y-%m-%d")
                    if not (start <= current <= end):
                        continue
                if date_str in cls._cache_loaded_dates:
                    continue

                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    try:
                        data = json.loads(fernet.decrypt(f.read()).decode())
                        for item in data:
                            for field, value in item.items():
                                cls._indexes[clsname][field].insert([str(value)], item)
                    except:
                        continue
                cls._cache_loaded_dates.add(date_str)

    @classmethod
    def _search_with_index(cls, filters, date_range=None, limit: Optional[int] = None):
        clsname = cls.__name__

        if clsname not in cls._indexes:
            cls._indexes[clsname] = {f: TreeNode() for f in cls._declared_fields}
        fernet = get_fernet_key(cls._password)

        def parse_lookup(key):
            if "__" in key:
                field, op = key.split("__", 1)
            else:
                field, op = key, "exact"
            return field, op

        def match_item(item, filters):
            for raw_key, value in filters.items():
                field, op = parse_lookup(raw_key)
                field_val = item.get(field)

                if op == "exact":
                    if str(field_val) != str(value): return False
                elif op == "contains":
                    if str(value) not in str(field_val): return False
                elif op == "icontains":
                    if str(value).lower() not in str(field_val).lower(): return False
                elif op == "gt":
                    if not (field_val > value): return False
                elif op == "lt":
                    if not (field_val < value): return False
                elif op == "in":
                    if field_val not in value: return False
                else:
                    return False
            return True

        matched_files = []
        for root, _, files in os.walk(cls._db_root):
            for file in files:
                if not file.endswith(".pu") or not file.startswith(clsname):
                    continue
                path_parts = root.split(os.sep)[-3:]
                date_str = "-".join(path_parts)
                if date_range:
                    start, end = map(lambda d: datetime.strptime(d, "%Y-%m-%d"), date_range)
                    current = datetime.strptime(date_str, "%Y-%m-%d")
                    if not (start <= current <= end):
                        continue
                matched_files.append((date_str, os.path.join(root, file)))

        matched_files.sort(key=lambda x: x[0], reverse=True)

        results = []
        for date_str, file_path in matched_files:
            try:
                with open(file_path, "rb") as f:
                    decrypted = fernet.decrypt(f.read())
                    items = json.loads(decrypted.decode())
            except:
                continue

            for item in items:
                if match_item(item, filters):
                    results.append(cls.from_dict(item))
                    if limit and len(results) >= limit:
                        return results

                if date_str not in cls._cache_loaded_dates:
                    for field, value in item.items():
                        cls._indexes[clsname][field].insert([str(value)], item)

            cls._cache_loaded_dates.add(date_str)

        return results

    @classmethod
    def update(cls, match_filters, **update_fields):
        objs = cls.objects().filter(**match_filters).all()
        for obj in objs:
            for k, v in update_fields.items():
                setattr(obj, k, v)
            obj.save()
        return len(objs)

    @classmethod
    def delete(cls, **filters):
        removed = 0
        fernet = get_fernet_key(cls._password)
        for root, _, files in os.walk(cls._db_root):
            for file in files:
                if not file.endswith('.pu') or not file.startswith(cls.__name__):
                    continue
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    try:
                        data = json.loads(fernet.decrypt(f.read()).decode())
                    except:
                        continue
                new_data = []
                for item in data:
                    if all(item.get(k) == v for k, v in filters.items()):
                        removed += 1
                        continue
                    new_data.append(item)
                with open(file_path, 'wb') as f:
                    f.write(fernet.encrypt(json.dumps(new_data).encode()))
        return removed


def create_base_model(connection_string: str):
    pattern = r"db://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<path>.+)"
    match = re.match(pattern, connection_string)
    if not match:
        raise ValueError("Invalid connection string format. Use: db://user:pass@/path/to/db")

    user = match.group("user")
    password = match.group("password")
    path = match.group("path").rstrip("/")

    auth = AuthManager()
    auth.login(user, password)

    class CustomBaseModel(BaseModel):
        _auth = auth
        _password = password
        _db_root = path
    CustomBaseModel.base_model = CustomBaseModel

    return CustomBaseModel