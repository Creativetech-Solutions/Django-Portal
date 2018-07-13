from django.shortcuts import render, redirect
import time
from django.http import HttpResponseRedirect,  HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json, locale , calendar, datetime
from django.conf import settings
from ops.Custom.Request import *
from dateutil.relativedelta import *
import csv
from calendar import monthrange

# Create your views here.
def index(request):
    # salt = hex(random.getrandbits(128)).encode()
    # return HttpResponse(len(salt))
    # dk = hashlib.pbkdf2_hmac('sha256',b'mypass',salt, 1000000)
    # return HttpResponse(binascii.hexlify(dk))
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")
        # do further call to get user information
    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+'}'
    r = Request()
    r = r.post(params, 'services', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    if 'isSuccess' in data:
        services = {'total_amt':0,'toll_calls_amt':0,'local_ditto_amt':0,'fax_amt':0,'st_charges_amt':0}
        if data['data']['services'] is not None:
            for index in data['data']['services']:
                services['total_amt'] += index['invoice_net_amount']
                services['toll_calls_amt'] += index['toll_traffic_amount']
                services['local_ditto_amt'] += index['local_traffic_amount']
                services['fax_amt'] += index['fax_traffic_amount']
                services['st_charges_amt'] += index['standing_charges_amount']
                   
        context = {'user_data': request.session['user_data']['user_info'], 'data':services}
        return render(request, 'portal/index.html', context)
    else:
        del request.session['user_data']
        request.session['errors'] = data['errors']
        return HttpResponseRedirect("/login")

def login(request):
    if 'errors' in request.session:
        context = {'errors':request.session['errors']}
        del request.session['errors']
    else:
        context = {'errors':''}
    return render(request, 'portal/login.html', context)

def home(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")
    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    context = {'user_data': request.session['user_data']['user_info']}
    return render(request, 'portal/home.html', context)

@csrf_exempt
def proccessLogin(request):
    if request.method == "POST":
        if(request.POST['account'] and request.POST['pass']):
            try:
                username = request.POST['account']
                password = request.POST['pass']
                
                # send request to api
                params = '{"username":'+username+',"password":"'+password+'"}'
                r = Request()
                r = r.post(params, 'login')
                data = r.json()
                if data['isSuccess'] and checkUserType(data['data']['user_info']['type']):
                    # save tokens in session
                    request.session['user_data'] = data['data']
                    return redirect("maintainAccountView",client_id=608)
                else:
                    request.session['errors'] = data['errors']
                    return HttpResponseRedirect("/login")
            except ValueError:
                request.session['error'] = 'Account and Password do not match'
        else :
            request.session['error'] = 'Account and Password do not match'
    else:
        request.session['error'] = 'Invalid Request Method'
    return HttpResponseRedirect("/login")

def createAccountView(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")
    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    context = {'user_data': request.session['user_data']['user_info']}
    return render(request, 'portal/account/create.html', context)

@csrf_exempt
def createAccount(request):
    if request.method == "POST":
        staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
        # send request to api
        post_data = request.POST
        if 'client_id' in post_data and post_data['client_id'] != "":
            url = "clients/edit"
        else:
            url = "clients/create"

        params = '{"staff_id":'+staff_id+', "data":'+json.dumps(post_data)+'}'
        r = Request()
        r = r.post(params, url, request.session['user_data']['tokens']['access_token'])
        data = r.json()
        if 'client_id' in data['data']['client'] and data['data']['client']['client_id'] != 0:
            msg = 'Account created with id : '+str(data['data']['client']['client_id'])
            data = {'alert':'success','message':msg}
        elif 'client_updated' in data['data']['client']:
            data = {'alert':'success', 'message':"Account Updated"}
        else:
            data = {'alert':'error','message':data['data']['client']['msg']}
        return HttpResponse(json.dumps(data))

def maintainAccountView(request, client_id=""):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+', "client_id":"'+str(client_id)+'"}'
    r = Request()
    data = r.get(params, 'clients/getClients', request.session['user_data']['tokens']['access_token'])
    data = data.json()
    if data['isSuccess']:
        # get rate plans
        r = Request()
        rate_plans = r.get(params, 'plans/getRatePlans', request.session['user_data']['tokens']['access_token'])
        data['rate_plans'] = rate_plans.json()['data']['rate_plans']

        context = {'user_data': request.session['user_data']['user_info'],'data':data}
        return render(request, 'portal/account/maintain.html', context)

    return HttpResponseRedirect("/login")

def getBusinessTypes(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+'}'
    r = Request()
    r = r.get(params, 'business/getBusinessTypes', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/dropdown_list.html', {'data':data})

def getAreaNames(request, area_code = ""):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    if area_code != "":
        params = '{"staff_id":'+staff_id+', "area_code":'+area_code+'}'
    else:
        params = '{"staff_id":'+staff_id+'}'

    r = Request()
    r = r.get(params, 'area/getAreaNames', request.session['user_data']['tokens']['access_token'])

    if area_code == "":
        data = r.json()
        return render(request, 'portal/account/dropdown_list.html', {'data':data})
    else:
        return HttpResponse(r)

def getIndustries(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+'}'
    r = Request()
    r = r.get(params, 'industry/getIndustries', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/dropdown_list.html', {'data':data})

def getCountries(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+'}'
    r = Request()
    r = r.get(params, 'country/getCountries', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/dropdown_list.html', {'data':data})

def getPaymentOptions(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+'}'
    r = Request()
    r = r.get(params, 'payment/getPaymentOptions', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/dropdown_list.html', {'data':data})

def getAllStaffs(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+'}'
    r = Request()
    r = r.get(params, 'staff/getAllStaffs', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/dropdown_list.html', {'data':data})

def getLineTypes(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+'}'
    r = Request()
    r = r.get(params, 'linetypes/getLineTypes', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/dropdown_list.html', {'data':data})

def getInvoices(request, clientId):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+',"client_id":"'+clientId+'", "limit":"1"}'
    r = Request()
    r = r.get(params, 'clients/getInvoices', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/tabs/acc_invoice.html', {'data':data})

def getOneoffinvoices(request, clientId):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+',"client_id":"'+clientId+'", "limit":"1"}'
    r = Request()
    r = r.get(params, 'clients/getOneOffInvoices', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    oneoffinvoices = []
    for index in data['data']['oneoffinvoices']:
        temp = {}
        temp['invoice_number'] = index['invoice_number']
        temp['invoice_date'] = index['invoice_date']
        temp['oi_description'] = index['oi_description']
        temp['oi_gross_amount'] = '$' +str(index['oi_gross_amount'])
        temp['credits'] = '$ 0.00'
        temp['payments'] = '$ 0.00'
        temp['total_amount'] = '$'+str(index['oi_gross_amount'])
        temp['oi_transaction_id'] = index['oi_transaction_id']

        oneoffinvoices.append(temp)
    return HttpResponse(json.dumps({'aaData':oneoffinvoices}))

def getOneOffCharges(request, clientId):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])

    params = {"staff_id":staff_id,"client_id":clientId}

    # send request to api
    if 'charges_id' in request.GET:
        if request.GET['charges_id'] != '0':
            params['other_charges_transaction_id'] = request.GET['charges_id']
        else:
            return render(request, 'portal/account/tabs/charges_detail.html', {'oneoff_charges':{'client_id':clientId}})
   
    r = Request()
    r = r.get(json.dumps(params), 'clients/getOneOffCharges', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    if 'charges_id' in request.GET: # mobile detail.html
        return render(request, 'portal/account/tabs/charges_detail.html', {'oneoff_charges':data['data']['oneoffcharges'][0]})
    else:
        return HttpResponse(json.dumps({'aaData':data['data']['oneoffcharges']}))

@csrf_exempt
def searchClient(request):
    if request.method == "POST":
        if 'user_data' not in request.session :
            return HttpResponseRedirect("/login")

        staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
        # user search string
        search_str = request.POST['search_str']
        params = '{"staff_id":'+staff_id+', "limit":"20", "search_str":"'+search_str+'"}'
        r = Request()
        r = r.post(params, 'clients', request.session['user_data']['tokens']['access_token'])
        data = r.json()
        return render(request, 'portal/components/search_result.html',{'data':data})

def getCredits(request, clientId):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+',"client_id":"'+clientId+'"}'
    r = Request()
    r = r.get(params, 'clients/getCredits', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/tabs/acc_credits.html', {'data':data})

def getCompanyPositions(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+'}'
    r = Request()
    r = r.get(params, 'positions/getCompanyPositions', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/dropdown_list.html', {'data':data})

def getMobilePlans(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+'}'
    r = Request()
    r = r.get(params, 'plans/getMobilePlans', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/dropdown_list.html', {'data':data})

def getMobileGroupPlans(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+'}'
    r = Request()
    r = r.get(params, 'plans/getMobileGroupPlans', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/dropdown_list.html', {'data':data})

def getServiceProviders(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+'}'
    r = Request()
    r = r.get(params, 'providers/getServiceProviders', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/dropdown_list.html', {'data':data})

def getAccountSummary(request, clientId):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = json.dumps({"staff_id":staff_id,"client_id":clientId})
    r = Request()
    r = r.get(params, 'clients/getAccountSummary', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/tabs/acc_account_summary.html', {'data':data})

def getPayments(request, clientId):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = '{"staff_id":'+staff_id+',"client_id":"'+clientId+'"}'
    r = Request()
    r = r.get(params, 'clients/getPayments', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    return render(request, 'portal/account/tabs/acc_payments.html', {'data':data})

def getContacts(request, clientId):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = {"staff_id":staff_id,"client_id":clientId}
    if 'contactId' in request.GET:
        if request.GET['contactId'] != '0':
            params['contact_id'] = request.GET['contactId']
        else:
            return render(request, 'portal/account/tabs/cont_contact_detail.html', {'contact':{'client_id':clientId}})

    params = json.dumps(params)
    r = Request()
    r = r.get(params, 'clients/getContacts', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    if 'contactId' in request.GET:
        return render(request, 'portal/account/tabs/cont_contact_detail.html', {'contact':data['data']['contacts'][0]})
    else:
        return HttpResponse(json.dumps({'aaData':data['data']['contacts']}))

def getClientPhones(request, clientId):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = {"staff_id":staff_id,"client_id":clientId}
    if 'phoneId' in request.GET:
        if request.GET['phoneId'] != '0':
            params['phone_id'] = request.GET['phoneId']
        else:
            return render(request, 'portal/account/tabs/ph_phone_detail.html', {'phone':{'client_id':clientId}})

    params = json.dumps(params)
    r = Request()
    r = r.get(params, 'clients/getClientPhones', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    if 'phoneId' in request.GET:
        return render(request, 'portal/account/tabs/ph_phone_detail.html', {'phone':data['data']['client_phones'][0]})
    elif 'type' in request.GET and request.GET['type'] == 'dropdown':
        return render(request, 'portal/account/dropdown_list.html', {'data':data})
    else:
        return HttpResponse(json.dumps({'aaData':data['data']['client_phones']}))

def getMobiles(request, clientId):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = {"staff_id":staff_id,"client_id":clientId}
    if 'mobileId' in request.GET:
        if request.GET['mobileId'] != '0':
            params['mobileId'] = request.GET['mobileId']
        else:
            return render(request, 'portal/account/tabs/mobile_detail.html', {'phone':{'client_id':clientId}})

    params = json.dumps(params)
    r = Request()
    r = r.get(params, 'clients/getMobiles', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    if 'mobileId' in request.GET: # mobile detail.html
        return render(request, 'portal/account/tabs/ph_phone_detail.html', {'phone':data['data']['client_mobiles'][0]})
    else:
        return HttpResponse(json.dumps({'aaData':data['data']['client_mobiles']}))

def getTollFree(request, clientId):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    # send request to api
    params = {"staff_id":staff_id,"client_id":clientId}
    if 'id' in request.GET:
        if request.GET['id'] != '0':
            params['client_toll_free_id'] = request.GET['id']
        else:
            return render(request, 'portal/account/tabs/toll_free_detail.html', {'toll_free':{'client_id':clientId}})

    params = json.dumps(params)
    r = Request()
    r = r.get(params, 'clients/getTollFree', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    if 'id' in request.GET: # mobile detail.html
        return render(request, 'portal/account/tabs/toll_free_detail.html', {'toll_free':data['data']['toll_free'][0]})
    elif 'type' in request.GET and request.GET['type'] == 'dropdown':
        return render(request, 'portal/account/dropdown_list.html', {'data':data})
    else:
        return HttpResponse(json.dumps({'aaData':data['data']['toll_free']}))

def getStandingCharges(request, clientId):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])

    params = {"staff_id":staff_id,"client_id":clientId}

    # send request to api
    if 'standing_charge_id' in request.GET:
        if request.GET['standing_charge_id'] != '0':
            params['standing_charge_id'] = request.GET['standing_charge_id']
        else:
            return render(request, 'portal/account/tabs/st_charges_detail.html', {'standing_charges':{'client_id':clientId}})
   
    r = Request()
    r = r.get(json.dumps(params), 'clients/getStandingCharges', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    if 'standing_charge_id' in request.GET: # mobile detail.html
        return render(request, 'portal/account/tabs/st_charges_detail.html', {'standing_charges':data['data']['standing_charges'][0]})
    else:
        return HttpResponse(json.dumps({'aaData':data['data']['standing_charges']}))

def getWhitelabel(request, clientId):
    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])

    params = {"staff_id":staff_id,"client_id":clientId}

    # send request to api
    r = Request()
    if request.GET['wl_enabled'] and request.GET['wl_enabled'] == 'False':

        if 'action' in request.GET and request.GET['action'] == 'read':
            return render(request, 'portal/account/controls_sidebar/wl_form.html')

        r = r.post(json.dumps(params), 'prices/getDefaultPrices', request.session['user_data']['tokens']['access_token'])
        data = r.json()
        data['data']['prices_default']['client_id'] = clientId
        return render(request, 'portal/account/controls_sidebar/enable_wl.html', {'white_label':data['data']['prices_default']})
   
    r = Request()
    r = r.get(json.dumps(params), 'clients/getWhitelabel', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    if 'action' in request.GET and request.GET['action'] == 'read':
        return render(request, 'portal/account/controls_sidebar/wl_form.html', {'white_label':data['data']['white_label']})
    else:
        return render(request, 'portal/account/controls_sidebar/enable_wl.html', {'white_label':data['data']['white_label']})

@csrf_exempt
def createOneOffCharges(request, clientId):
    if request.method == "POST":
        staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
        post_data = request.POST
        params = '{"staff_id":'+staff_id+', "client_id":'+clientId+', "data":'+json.dumps(post_data)+'}'
        if 'other_charges_transaction_id' in post_data and post_data['other_charges_transaction_id'] != '':
            url = 'clients/updateOneOffCharges'
        else:
            url = 'clients/createOneOffCharges'

        r = Request()
        r = r.post(params, url, request.session['user_data']['tokens']['access_token'])
        data = r.json()

        if 'other_charges_transaction_id' in post_data and post_data['other_charges_transaction_id'] != '':
            if data['data']['one_off_charge']['charge_updated']:
                msg = 'One-Off Charge updated'
                data = {'alert':'success','message':msg}
            else:
                data = {'alert':'error','message':'One-Off Charge not updated'}
        else:
            if data['data']['one_off_charge']['charge_created']:
                msg = 'One-Off Charge created'
                data = {'alert':'success','message':msg}
            else:
                data = {'alert':'error','message':'One-Off Charge not creaded'}

        return HttpResponse(json.dumps(data))
@csrf_exempt
def createContact(request, clientId):
    if request.method == "POST":
        staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
        post_data = request.POST
        params = '{"staff_id":'+staff_id+', "client_id":'+clientId+', "data":'+json.dumps(post_data)+'}'
        if 'contact_id' in post_data and post_data['contact_id'] != '':
            url = 'clients/updateContact'
        else:
            url = 'clients/createContact'

        r = Request()
        r = r.post(params, url, request.session['user_data']['tokens']['access_token'])
        data = r.json()

        if 'contact_id' in post_data and post_data['contact_id'] != '':
            if data['data']['contact']['contact_updated']:
                msg = 'Contact Updated'
                data = {'alert':'success','message':msg}
            else:
                data = {'alert':'error','message':'Contact not updated'}
        else:
            if data['data']['contact']['contact_created']:
                msg = 'Contact created'
                data = {'alert':'success','message':msg}
            else:
                data = {'alert':'error','message':'Contact not creaded'}

        return HttpResponse(json.dumps(data))

@csrf_exempt
def createPhone(request, clientId):
    if request.method == "POST":
        staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
        post_data = request.POST
        params = '{"staff_id":'+staff_id+', "client_id":'+clientId+', "data":'+json.dumps(post_data)+'}'
        if 'client_to_phone_id' in post_data and post_data['client_to_phone_id'] != '':
            url = 'clients/updatePhone'
        else:
            url = 'clients/createPhone'

        r = Request()
        r = r.post(params, url, request.session['user_data']['tokens']['access_token'])
        data = r.json()

        if 'client_to_phone_id' in post_data and post_data['client_to_phone_id'] != '':
            if data['data']['phone']['phone_updated']:
                msg = 'Phone Updated'
                data = {'alert':'success','message':msg}
            else:
                data = {'alert':'error','message':'Phone not updated'}
        else:
            if data['data']['phone']['phone_created']:
                msg = 'Phone created'
                data = {'alert':'success','message':msg}
            else:
                data = {'alert':'error','message':'Phone not creaded'}

        return HttpResponse(json.dumps(data))

@csrf_exempt
def createTollfree(request, clientId):
    if request.method == "POST":
        staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
        post_data = request.POST
        params = '{"staff_id":'+staff_id+', "client_id":'+clientId+', "data":'+json.dumps(post_data)+'}'
        if 'client_toll_free_id' in post_data and post_data['client_toll_free_id'] != '':
            url = 'clients/updateTollfree'
        else:
            url = 'clients/createTollfree'

        r = Request()
        r = r.post(params, url, request.session['user_data']['tokens']['access_token'])
        data = r.json()

        if 'client_toll_free_id' in post_data and post_data['client_toll_free_id'] != '':
            if data['data']['tollfree']['tollfree_updated']:
                msg = 'Tollfree Updated'
                data = {'alert':'success','message':msg}
            else:
                data = {'alert':'error','message':'Tollfree not updated'}
        else:
            if data['data']['tollfree']['tollfree_created']:
                msg = 'Tollfree created'
                data = {'alert':'success','message':msg}
            else:
                data = {'alert':'error','message':'Tollfree not creaded'}

        return HttpResponse(json.dumps(data))

@csrf_exempt
def createStandingCharges(request, clientId):
    if request.method == "POST":
        staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
        post_data = request.POST
        params = '{"staff_id":'+staff_id+', "client_id":'+clientId+', "data":'+json.dumps(post_data)+'}'
        if 'standing_charge_id' in post_data and post_data['standing_charge_id'] != '':
            url = 'clients/updateStandingCharges'
        else:
            url = 'clients/createStandingCharges'

        r = Request()
        r = r.post(params, url, request.session['user_data']['tokens']['access_token'])
        data = r.json()

        if 'standing_charge_id' in post_data and post_data['standing_charge_id'] != '':
            if data['data']['standing_charges']['st_charges_updated']:
                msg = 'Standing charges Updated'
                data = {'alert':'success','message':msg}
            else:
                data = {'alert':'error','message':'Standing charges not updated'}
        else:
            if data['data']['standing_charges']['st_charges_created']:
                msg = 'Standing charges created'
                data = {'alert':'success','message':msg}
            else:
                data = {'alert':'error','message':'Standing charges not creaded'}

        return HttpResponse(json.dumps(data))

@csrf_exempt
def createWhiteLabel(request, clientId):
    if request.method == "POST":
        staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
        post_data = request.POST
        params = '{"staff_id":'+staff_id+', "client_id":'+clientId+', "data":'+json.dumps(post_data)+'}'
        if 'wl_client_id' in post_data and post_data['wl_client_id'] != '':
            url = 'clients/updateWhiteLabel'
        else:
            url = 'clients/createWhiteLabel'

        r = Request()
        r = r.post(params, url, request.session['user_data']['tokens']['access_token'])
        data = r.json()

        if 'wl_client_id' in post_data and post_data['wl_client_id'] != '':
            if data['data']['white_label']['whitelabel_updated']:
                msg = 'Client White Label Updated'
                data = {'alert':'success','message':msg,'action':'createWl'}
            else:
                data = {'alert':'error','message':'Client White Label not updated'}
            return HttpResponse(json.dumps(data))

# partner page

def maintainPartnerView(request, partner_id=""):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])

    # send request to api
    params = '{"staff_id":'+staff_id+', "partner_id":'+partner_id+'}'
    r = Request()
    r = r.get(params, 'staff/getStaff', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    if data['isSuccess']:
        context = {'user_data': request.session['user_data']['user_info'],'data':data}
        return render(request, 'portal/partner_account/maintain.html', context)
    return HttpResponseRedirect("/login")

@csrf_exempt
def editPartner(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")

    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
    post_data = request.POST
    # send request to api
    params = '{"staff_id":'+staff_id+', "data":'+json.dumps(post_data)+'}'
    r = Request()
    r = r.post(params, 'staff/editStaff', request.session['user_data']['tokens']['access_token'])
    data = r.json()
    if 'staff_and_agents_id' in post_data and post_data['staff_and_agents_id'] != '':
        if data['data']['staff']['staff_updated']:
            msg = 'Staff  Updated'
            data = {'alert':'success','message':msg}
        else:
            data = {'alert':'error','message':'Staff not updated'}
    else:
        if data['data']['staff']['staff_created']:
            msg = 'Staff created'
            data = {'alert':'success','message':msg}
        else:
            data = {'alert':'error','message':'Staff not creaded'}
    return HttpResponse(json.dumps(data))


@csrf_exempt
def searchPartner(request):
    if request.method == "POST":
        if 'user_data' not in request.session :
            return HttpResponseRedirect("/login")

        staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
        # user search string
        search_str = request.POST['search_str']
        params = '{"staff_id":'+staff_id+', "limit":"20", "search_str":"'+search_str+'"}'
        r = Request()
        r = r.get(params, 'staff/getAllStaffs', request.session['user_data']['tokens']['access_token'])
        data = r.json()
        return render(request, 'portal/components/search_result.html',{'data':data})


def getClients(request, partner_id=""):
        staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
        # user search string
        params = '{"staff_id":'+staff_id+', "partner_id":'+partner_id+'}'
        r = Request()
        r = r.get(params, 'clients/getClients', request.session['user_data']['tokens']['access_token'])
        data = r.json()
        return HttpResponse(json.dumps({'aaData':data['data']['clients']}))

def getcreateAccountPage(request):
    return render(request, 'portal/account/create_content.html')


def logout(request):
    try:
        if(request.session['user_data']):
            del request.session['user_data']
            return HttpResponseRedirect("/login")
    except:
        return HttpResponseRedirect("/login")

def checkUserType(userType):
    if (userType == '3'):
        return True
    else:
        return False

def checkUserSession(request):
    if 'user_data' not in request.session :
        return HttpResponseRedirect("/login")
    staff_id = str(request.session['user_data']['user_info']['staff_and_agents_id'])
