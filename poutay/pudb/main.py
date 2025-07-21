from orm import Field, ManyToManyField, create_base_model, ForeignKey

BaseModel = create_base_model("db://admin:123456@mydb")

class Order(BaseModel):
    customer = Field("مشتری")
    product = Field("محصول")
    amount = Field("مقدار")

class Author(BaseModel):
    id = Field()
    name = Field()

class Book(BaseModel):
    id = Field("id")
    title = Field("title",default = "1234")
    authors = ManyToManyField(Author, related_name="books")

class Author1(BaseModel):
    name = Field("نام")

class Book1(BaseModel):
    title = Field("عنوان", default="title")
    author = ForeignKey(to_model=Author1, related_name="books")


a1 = Author1(name="Orwell")
a1.save()

b1 = Book1( author=a1.id)
b1.save()

b2 = Book1(title="Animal Farm", author=a1.id)
b2.save()

for b in a1.books.all():   # `books` از related_name آمده
    print(b.title)

book = Book(title="1984")
book.save()

a1 = Author(name="Orwell"); a1.save()
a2 = Author(name="Smith"); a2.save()

book.authors.add(a1, a2)

for author in book.authors.filter(name__contains="Orwe"):
    print(author.name)

# دسترسی از طرف مقابل
for book in a1.books.filter(title=1984):
    print(book.title)

print(book.authors.all()[0])
# ذخیره رکورد
Order(customer="Ali", product="Laptop", amount=1).save()
# Order(customer="Sara", product="Phone", amount=2).save()

# جستجو ساده
results = Order.objects().filter(product="Laptop").all()
for i in results:
    print(i.__dict__)

# جستجو بر اساس تاریخ
# results = Order.objects().filter(customer="Ali").between("2025-07-01", "2025-07-10").all()
#
# # صفحه‌بندی
# paged = Order.objects().filter().paginate(page=1, per_page=2)
#
# # بروزرسانی
# Order.update({"customer": "Ali"}, id=3)
#
# # حذف
# Order.delete(customer="Ali")
