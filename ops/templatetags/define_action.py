from django import template
register = template.Library()

@register.simple_tag
def define(val=None):
  return val

@register.filter
def amountFormat(value, arg=None):
	if value == "" or value == None:
		return '$ 0.00'
	return "$ "+"{:0,.2f}".format(value)

@register.filter
def noneCheck(value, arg=None):
	if value == None:
		return ''
	return value

@register.filter
def active_route(request, path):
	if path in request.path:
		return 'active'
	return ''

@register.filter
def empty_dashes(value, arg=None):
	if value == None or value == '':
		return '------'
	return value

@register.filter
def page_heading(path, arg=None):
	if 'account/maintain' in path:
		return 'Maintain Account'
	elif 'partner/maintain' in path:
		return 'Maintain Partner'
	elif 'account/create' in path:
		return 'Create Account'
	return ''

@register.filter
def quantityCheck(qty, arg=None):
	if qty == None or qty == 0 or qty == '':
		return 1
	return qty

@register.filter
def divide(divider, dividend):
	return dividend/divider
