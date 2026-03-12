def user_role(request):
    role = request.session.get('user_role', 'Operator')
    if role not in ['Operator', 'SDM', 'Pimpinan']:
        role = 'Operator'
    return {'user_role': role}
