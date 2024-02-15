from django.shortcuts import render,redirect

from django.views.generic import View

from budget.models import Transaction

from django import forms

from django.contrib.auth.models import User

from django.contrib.auth import authenticate,login,logout

from django.utils import timezone

from django.db.models import Sum

from django.utils.decorators import method_decorator

from django.contrib import messages

from django.views.decorators.cache import never_cache



def signin_required(Fn):

    def wrapper(request,*args,**kwargs):
        if not request.user.is_authenticated:
            messages.error(request,"invalid session")
            return redirect("signin")
        else:
            return Fn(request,*args,**kwargs)
        
    return wrapper

decs=[signin_required,never_cache]

class TransactionForm(forms.ModelForm):


    class Meta:
        model=Transaction
        exclude=("created_date","user_object")
        # fields=__all__
        # fields=["field1","field2",..]
        widgets={
            "title":forms.TextInput(attrs={"class":"form-control"}),
            "amount":forms.NumberInput(attrs={"class":"form-control"}),
            "type":forms.Select(attrs={"class":"form-control form-select"}),
            "category":forms.Select(attrs={"class":"form-control form-select"}),

        }

# registration form
        
class RegistrationForm(forms.ModelForm):

    class Meta:
        model=User
        fields=["username","email","password"]

        widgets={
            "username":forms.TextInput(attrs={"class":"form-control"}),
            "email":forms.EmailInput(attrs={"class":"form-control"}),
            "password":forms.PasswordInput(attrs={"class":"form-control"})
        }


# loginform
class LoginForm(forms.Form):
    username=forms.CharField(widget=forms.TextInput(attrs={"class":"form-control"}))
    password=forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control"}))


# view for listing all transactions
# url = localhost:8000/transactions/all/

@method_decorator(decs,name="dispatch")
class TransactionListView(View):
    def get(self,request,*args,**kwargs):
        qs=Transaction.objects.filter(user_object=request.user)
        # print(qs.query) : for getting the corresponding mysql qs type query set
        cur_month=timezone.now().month
        cur_year=timezone.now().year
        # print(cur_month,cur_year)

        # expense_tot=Transaction.objects.filter(
        #     user_object=request.user,
        #     type="expense",
        #     created_date__month=cur_month,
        #     created_date__year=cur_year
        # ).aggregate(Sum("amount"))
        # print(expense_tot)
        # income_tot=Transaction.objects.filter(
        #     user_object=request.user,
        #     type="income",
        #     created_date__month=cur_month,
        #     created_date__year=cur_year
        # ).aggregate(Sum("amount"))
        # print(income_tot)

        data=Transaction.objects.filter(
            created_date__month=cur_month,
            created_date__year=cur_year,
            user_object=request.user
        ).values("type").annotate(type_sum=Sum("amount"))
        print(data)

        cat_data=Transaction.objects.filter(
            created_date__month=cur_month,
            created_date__year=cur_year,
            user_object=request.user
        ).values("category").annotate(cat_sum=Sum("amount"))
        print(cat_data)
        
        return render(request,"transaction_list.html",{"data":qs,"type_total":data,"category_total":cat_data})
    
# view for creating transaction
# url:localhost:8000/transactions/all/
    
@method_decorator(decs,name="dispatch")
class TransactionCreateView(View):
    def get(self,request,*args,**kwargs):
        form=TransactionForm()
        return render(request,"transaction_add.html",{"form":form})
    
    def post(self,request,*args,**kwargs):
        form=TransactionForm(request.POST)
        if form.is_valid():
            # data=cleaned_data
            # Transaction.objects.create()
            # form.save()
            # form.instance.user_object=request.user  : only in modelform
            data=form.cleaned_data
            Transaction.objects.create(**data,user_object=request.user)
            messages.success(request,"Transaction has been added successfully")
            return redirect("transaction-list")
        else:
             messages.error(request,"Failed to add transaction")
             return render(request,"transaction_add.html",{"form":form})


# url : localhost:8000/transactions/{id}/
# get method
        
@method_decorator(decs,name="dispatch")
class TransactionDetailView(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        qs=Transaction.objects.get(id=id)
        return render(request,"transaction_detail.html",{"data":qs})
    
# transaction delete view starts
# url : localhist:8000/id/remove/
# get method

@method_decorator(decs,name="dispatch")
class TransactionDeleteView(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        Transaction.objects.filter(id=id).delete()
        messages.success(request,"Transaction has been deleted")
        return redirect("transaction-list")
    
# transaction update view
# get and post method 
@method_decorator(decs,name="dispatch")
class TransactionUpdateView(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        transaction_object=Transaction.objects.get(id=id)
        form=TransactionForm(instance=transaction_object)
        return render(request,"transaction_edit.html",{"form": form})

    def post(self,request,*args,**kwargs):
        
        id=kwargs.get("pk")
        transaction_object=Transaction.objects.get(id=id)
        form=TransactionForm(request.POST,instance=transaction_object)
        if form.is_valid():
            form.save()
            messages.success(request,"Transaction has been updated successfully")
            return redirect("transaction-list")
        else:
            messages.error(request,"Failed to update transaction")
            return render(request,"transaction_edit.html",{"form": form})


# registration view
# url:localhost:8000/signup/
# get,post method
class SignUpView(View):
    def get(self,request,*args,**kwargs):
        form=RegistrationForm()
        return render(request,"registration.html",{"form":form})
    def post(self,request,*args,**kwargs):
        form=RegistrationForm(request.POST)
        if form.is_valid():
            # form.save()=we cant use,to encrypt data
            User.objects.create_user(**form.cleaned_data)
            print("account created")
            return redirect("signin")
        else:
            print("failed")
            return render(request,"registration.html",{"form":form})
        

# sign in view
# url localhost:8000/signin/
# grt,post method


class SignInView(View):
    def get(self,request,*args,**kwargs):
        form=LoginForm()
        return render(request,"signin.html",{"form":form})
    def post(self,request,*args,**kwargs):
        form=LoginForm(request.POST)
        if form.is_valid():
            u_name=form.cleaned_data.get("username")
            pwd=form.cleaned_data.get("password")
            user_object=authenticate(request,username=u_name,password=pwd)
            if user_object:
                # print("valid")
                login(request,user_object)
                # request.user=prints the user which logined there
                # anonymous user=if session expired or the user did n't login
                return redirect("transaction-list")
            
        return render(request,"signin.html",{"form":form})
    
# sign out view starts
@method_decorator(decs,name="dispatch")  
class SignOutView(View):
    def get(self,request,*args,**kwargs):
        logout(request)
        return redirect("signin")
