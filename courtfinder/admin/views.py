import json
import forms
import storage
from collections import OrderedDict as odict
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.forms import PasswordChangeForm, AdminPasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from geolocation import mapit
from search import models
from django.views import View
from .models import FacilityType, ContactType, OpeningType


@permission_required('emergency')
def emergency_message(request):
    msg = models.EmergencyMessage.objects.all().first()
    if request.method == 'POST':
        form = forms.EmergencyMessageForm(request.POST, instance=msg)
        if form.is_valid():
            form.save()
            messages.success(request, 'Emergency message updated')
            messages.warning(request, 'The message is now *%s*' % ('visible' if msg.show else 'hidden'))
            return redirect('admin:emergency')
    else:
        form = forms.EmergencyMessageForm(instance=msg)

    return render(request, 'emergency.html', {
        'form': form
    })


def courts(request):
    sort = request.GET.get('sort')
    order = sort if sort in ('name', 'updated_at') else 'name'
    return render(request, 'court/list.html', {
        'courts': models.Court.objects.order_by(order).all()
    })


@permission_required('user.manage')
def users(request):
    return render(request, 'user/list.html', {
        'users': User.objects.order_by('username').all()
    })


@permission_required('user.manage')
def add_user(request):
    if request.method == 'POST':
        form = forms.UserAddForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            messages.success(request, '`%s` has been added' % new_user.username)
            return redirect('admin:users')
    else:
        form = forms.UserAddForm()

    return render(request, 'user/add.html', {
        'form': form,
        'random_password': User.objects.make_random_password()
    })


@permission_required('user.manage')
def edit_user(request, username):
    user = get_object_or_404(User, username=username)
    if request.method == 'POST':
        form = forms.UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, '`%s` has been updated' % user.username)
            return redirect('admin:edit_user', user.username)
    else:
        form = forms.UserEditForm(instance=user)

    return render(request, 'user/edit.html', {
        'username': user.username,
        'form': form,
        'delete_form': forms.UserDeleteForm()
    })


@permission_required('user.manage')
def change_user_password(request, username):
    user = get_object_or_404(User, username=username)
    if request.method == 'POST':
        form = AdminPasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '`%s` password has been updated' % user.username)
            return redirect('admin:edit_user', user.username)
    else:
        form = AdminPasswordChangeForm(user)

    return render(request, 'user/password.html', {
        'form': form,
        'username': user.username,
        'random_password': User.objects.make_random_password(),
    })


@require_POST
@permission_required('user.manage')
def delete_user(request, username):
    form = forms.UserDeleteForm(request.POST)
    if form.is_valid() and form.cleaned_data['username'] == username:
        user = get_object_or_404(User, username=username)
        user.delete()
        messages.success(request, '`%s` has been deleted' % username)
        return redirect('admin:users')
    else:
        messages.error(request, 'Could\'t delete user `%s`' % username)
        return redirect('admin:edit_user', username)


def account(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'account.html', {
        'form': form
    })


@permission_required('court.new')
def new_court(request):
    form = forms.CourtNewForm(request.POST if request.POST else None)
    if request.method == 'POST' and form.is_valid():
        court = form.save()
        messages.success(request, 'New court has been added')
        return redirect('admin:court', court.id)
    return render(request, 'court/new.html', {
        'form': form
    })


def edit_court(request, id):
    court = get_object_or_404(models.Court, pk=id)
    form = forms.CourtBasicForm(request.POST, court, request.user.has_perm('court.info'))
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Court information updated')
        court.update_timestamp()
        return redirect('admin:court', id)
    return render(request, 'court/basic.html', {
        'court': court,
        'form': form
    })


def edit_types(request, id):
    court = get_object_or_404(models.Court, pk=id)
    form = forms.CourtTypes(request.POST if request.POST else None, instance=court)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Court types updated')
        court.update_timestamp()
        return redirect('admin:types', court.id)

    return render(request, 'court/types.html', {
        'form': form,
        'court': court,
    })


def edit_location(request, id):
    court = get_object_or_404(models.Court, pk=id)
    if request.method == 'POST':
        form = forms.CourtLocationForm(request.POST, instance=court)
        if form.is_valid():
            form.save()
            messages.success(request, 'Location details updated')
            court.update_timestamp()
            return redirect('admin:location', id)
    else:
        form = forms.CourtLocationForm(instance=court)

    return render(request, 'court/location.html', {
        'court': court,
        'form': form,
        'postcode_form': forms.LocatePostcodeForm()
    })


@require_POST
def locate_postcode(request, id):
    court = get_object_or_404(models.Court, pk=id)
    form = forms.LocatePostcodeForm(request.POST)
    if form.is_valid():
        try:
            postcode = mapit.postcode(form.cleaned_data['postcode'])
            court.lat, court.lon = postcode.coordinates
            court.save()
            messages.success(request, 'Coordinates changed to %s, %s' % (court.lat, court.lon))
            court.update_timestamp()
        except mapit.MapitException as e:
            messages.error(request, 'Geolocation failed: %s' % e.message)
    else:
        messages.error(request, 'Geolocation failed')
    return redirect('admin:location', id)


def edit_address(request, id, address_id=None):
    court = get_object_or_404(models.Court, pk=id)
    if request.POST:
        form_index = int(request.POST["form_index"])
        if address_id:
            try:
                court_address = models.CourtAddress.objects.get(pk=address_id)
            except models.CourtAddress.DoesNotExist:
                court_address = None
        else:
            court_address = None
        form = forms.CourtAddressForm(data=request.POST or None, address_index=form_index, court=court, instance=court_address)
        if form.is_valid():
            court_address = form.save(commit=False)
            court_address.court = court
            court_address.save()
            messages.success(request, 'Address updated')
            court.update_timestamp()
        return redirect('admin:address', id)
    else:
        court_addresses = court.courtaddress_set.all().order_by('pk')
        court_address_forms = odict()
        for i, c in enumerate(court_addresses):
            c_address_form = forms.CourtAddressForm(instance=c, address_index=i, court=court)
            court_address_forms[c_address_form] = c.pk
        while len(court_address_forms) < 2:
            new_address = forms.CourtAddressForm(instance=None, address_index=len(court_address_forms), court=court)
            court_address_forms[new_address] = None
        return render(request, 'court/address.html', {
            'court': court,
            "court_address_forms": court_address_forms,
        })


@require_POST
def delete_address(request, id, address_id=None):
    court = get_object_or_404(models.Court, pk=id)
    try:
        court_address = models.CourtAddress.objects.filter(court=court).get(pk=address_id)
    except models.CourtAddress.DoesNotExist:
        court_address = None
    if court_address:
        court_address.delete()
        messages.success(request, 'Address deleted')
        court.update_timestamp()
    return redirect('admin:address', id)


class BaseFormView(View):
    template = None
    return_url = None
    reorder_url = None
    formset = None
    objects = None
    court = None
    ordering = False
    update_message = "Updated"
    heading = ""
    header_message = ""

    def get_context_data(self):
        pass

    def process_request(self, request):
        pass

    def initialize(self, request, id):
        pass

    def initialize_get(self, request, id):
        pass

    def get(self, request, *args, **kwargs):
        id = kwargs.get('id', None)
        self.initialize_get(request, id)
        return render(request, self.template, self.get_context_data())

    def post(self, request, *args, **kwargs):
        id = kwargs.get('id', None)
        self.initialize(request, id)
        self.process_request(request)
        return redirect(self.return_url)


class BaseOrderableFormView(BaseFormView):

    ordering = True

    def initialize(self, request, id):
        self.court = get_object_or_404(models.Court, pk=id)


class OrderableFormView(BaseOrderableFormView):
    template = 'court/orderable.html'

    def handle_instance_saving(self, instances):
        pass

    def process_request(self, request):
        formset = self.formset(request.POST)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()
            self.handle_instance_saving(instances)
            messages.success(request, self.update_message)
            self.court.update_timestamp()

    def get_context_data(self):
        formset = self.formset(queryset=self.objects)
        context = {
            'court': self.court,
            "formset": formset,
            "return_url": self.return_url,
            "reorder_url": self.reorder_url,
            "ordering": self.ordering,
            'heading': self.heading,
            'header_message': self.header_message,
        }
        return context


class ReorderingFormView(BaseOrderableFormView):
    template = 'court/reordering.html'

    def update_order(self, new_order):
        pass

    def process_request(self, request):
        if "new_sort_order" in request.POST:
            new_order = request.POST["new_sort_order"]
            if new_order:
                self.update_order(new_order)

    def get_context_data(self):
        context = {
            'court': self.court,
            "objects": self.objects,
            "return_url": self.return_url,
            "reorder_url": self.reorder_url,
            }
        return context


class ContactMixin(object):

    def initialize(self, request, id):
        super(ContactMixin, self).initialize(request, id)
        self.formset = modelformset_factory(models.Contact, forms.CourtContactForm, extra=1, can_delete=True)
        self.return_url = reverse("admin:contact", kwargs={'id': id})
        self.update_message = 'Contacts updated'

    def initialize_get(self, request, id):
        self.initialize(request, id)
        self.reorder_url = reverse("admin:reorder_contacts", kwargs={'id': id})
        self.objects = self.court.contacts.order_by('sort_order')
        self.heading = "Contacts"
        self.header_message = "The DX contact will show separately in the court header"

class ContactFormView(ContactMixin, OrderableFormView):

    def handle_instance_saving(self, instances):
        for instance in instances:
            if instance._state.adding:
                inst = instance.save()
                instance.sort_order = inst  # Sets the order of the new object to its id to preserve order
                instance.save(update_fields=["sort_order"])
                court_contact = models.CourtContact(court=self.court, contact=instance)
                court_contact.save()
            else:
                instance.save()


class ContactReorderView(ContactMixin, ReorderingFormView):

    def update_order(self, new_order):
        new_order = json.loads(new_order)
        for i, o in enumerate(new_order):
            try:
                court_contact = models.CourtContact.objects.get(court=self.court, contact=o)
            except models.CourtContact.DoesNotExist:
                pass
            if court_contact:
                contact = court_contact.contact
                contact.sort_order = i
                contact.save()


class EmailMixin(object):

    def initialize(self, request, id):
        super(EmailMixin, self).initialize(request, id)
        self.formset = modelformset_factory(models.Email, forms.CourtEmailForm, extra=1, can_delete=True)
        self.return_url = reverse("admin:email", kwargs={'id': id})
        self.update_message = 'Emails updated'

    def initialize_get(self, request, id):
        self.initialize(request, id)
        self.reorder_url = reverse("admin:reorder_emails", kwargs={'id': id})
        self.objects = self.court.emails.order_by('courtemail__order')
        self.heading = "Email addresses"


class EmailFormView(EmailMixin, OrderableFormView):

    def handle_instance_saving(self, instances):
        for instance in instances:
            if instance._state.adding:
                instance.save()
                court_email = models.CourtEmail(court=self.court, email=instance)
                court_email.save()
                court_email.order = court_email.pk  # Sets the order of the new object to its id to preserve order
                court_email.save(update_fields=["order"])
            else:
                instance.save()


class EmailReorderView(EmailMixin, ReorderingFormView):

    def update_order(self, new_order):
        new_order = json.loads(new_order)
        for i, o in enumerate(new_order):
            try:
                court_email = models.CourtEmail.objects.get(court=self.court, email=o)
            except models.CourtEmail.DoesNotExist:
                pass
            if court_email:
                court_email.order = i
                court_email.save()


class OpeningTimeMixin(object):

    def initialize(self, request, id):
        super(OpeningTimeMixin, self).initialize(request, id)
        self.formset = modelformset_factory(models.OpeningTime, forms.CourtOpeningForm, extra=1, can_delete=True)
        self.return_url = reverse("admin:opening", kwargs={'id': id})
        self.update_message = 'Opening times updated'

    def initialize_get(self, request, id):
        self.initialize(request, id)
        self.reorder_url = reverse("admin:reorder_openings", kwargs={'id': id})
        self.objects = self.court.opening_times.order_by('courtopeningtime__sort')
        self.heading = "Opening times"


class OpeningFormView(OpeningTimeMixin, OrderableFormView):

    def handle_instance_saving(self, instances):
        for instance in instances:
            if instance._state.adding:
                instance.save()
                court_opening = models.CourtOpeningTime(court=self.court, opening_time=instance)
                court_opening.save()
                court_opening.sort = court_opening.pk  # Sets the order of the new object to its id to preserve order
                court_opening.save(update_fields=["sort"])
            else:
                instance.save()


class OpeningReorderView(OpeningTimeMixin, ReorderingFormView):

    def update_order(self, new_order):
        new_order = json.loads(new_order)
        for i, o in enumerate(new_order):
            try:
                court_opening = models.CourtOpeningTime.objects.get(court=self.court, opening_time=o)
            except models.CourtEmail.DoesNotExist:
                pass
            if court_opening:
                court_opening.sort = i
                court_opening.save()
                
                
class FacilityMixin(object):

    def initialize(self, request, id):
        super(FacilityMixin, self).initialize(request, id)
        self.formset = modelformset_factory(models.Facility, forms.CourtFacilityForm, extra=1, can_delete=True)
        self.return_url = reverse("admin:facility", kwargs={'id': id})
        self.update_message = 'Facilities updated'
        self.ordering = False

    def initialize_get(self, request, id):
        self.initialize(request, id)
        self.reorder_url = reverse("admin:reorder_facilities", kwargs={'id': id})
        self.objects = self.court.facilities.all()
        self.heading = "Facilities"


class FacilityFormView(FacilityMixin, OrderableFormView):

    def handle_instance_saving(self, instances):
        for instance in instances:
            if instance._state.adding:
                instance.save()
                court_facility = models.CourtFacility(court=self.court, facility=instance)
                court_facility.save()
            else:
                if instance.name:
                    instance.save()


class FacilityReorderView(FacilityMixin, ReorderingFormView):

    def update_order(self, new_order):
        new_order = json.loads(new_order)
        for i, o in enumerate(new_order):
            try:
                court_facility = models.CourtFacility.objects.get(court=self.court, facility=o)
            except models.CourtEmail.DoesNotExist:
                pass
            if court_facility:
                court_facility.save()


def areas_of_law(request, id):
    court = get_object_or_404(models.Court, pk=id)
    form = forms.CourtAreasOfLawForm(request.POST if request.POST else None, instance=court)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Areas of law updated')
        court.update_timestamp()
        return redirect('admin:aols', court.id)

    return render(request, 'court/aols.html', {
        'form': form,
        'court': court,
    })


@permission_required('court.leaflets')
def edit_leaflets(request, id):
    court = get_object_or_404(models.Court, pk=id)
    form = forms.CourtLeafletsForm(request.POST if request.POST else None, instance=court)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Leaflets updated')
        court.update_timestamp()
        return redirect('admin:leaflets', court.id)
    return render(request, 'court/leaflets.html', {
        'court': court,
        'form': form
    })


def photo_upload(request, id):
    court = get_object_or_404(models.Court, pk=id)
    form = forms.UploadImageForm(request.POST, request.FILES)
    if request.method == 'POST':
        if form.is_valid():
            try:
                storage.upload_court_photo(court, form.cleaned_data['image'])
                messages.success(request, 'Photo uploaded')
                court.update_timestamp()
                return redirect('admin:photo', court.id)
            except storage.StorageException as e:
                messages.error(request, e)
    else:
        form = forms.UploadImageForm()

    return render(request, 'court/photo.html', {
        'form': form,
        'court': court,
        #todo for some reason court images aren't proxied trough nginx like other uploaded assets
        's3': settings.COURT_IMAGE_BASE_URL
    })


@require_POST
def photo_delete(request, id):
    court = get_object_or_404(models.Court, pk=id)
    try:
        storage.delete_court_photo(court)
        messages.success(request, 'Photo deleted')
        court.update_timestamp()
    except storage.StorageException as e:
        messages.error(request, e)
    return redirect('admin:photo', court.id)


class AdminListView(View):
    template = 'lists/list_view.html'
    objects = None
    partial = None
    heading = None
    header_message = None

    def initialize(self, request):
        pass

    def handle_instance_saving(self, instances):
        pass

    def get(self, request):
        self.initialize(request)
        return render(request, self.template, self.get_context_data())

    def get_context_data(self):
        context = {
            'heading': self.heading,
            'header_message': self.header_message,
            'objects': self.objects,
            'partial': self.partial,
        }
        return context


class FacilityList(AdminListView):

    def initialize(self, request):
        self.partial = "partials/facility_table_contents.html"
        facilities = [
            {
                'id': facility.id,
                # Name is used for the css class name to set the x,y offsets on old style images
                'name': facility.name,
                # Image class is the generated class name (empty for new style images)
                'image_class': "" if facility.image_file_path else 'icon-' + facility.image,
                # The relative path to the image
                'image_src': facility.image_file_path if facility.image_file_path else 'images/facility_icons.png',
                # This description is used for the alt text
                'image_description': facility.image_description,
                # The relative file path of the image
                'image_file_path': facility.image_file_path
            }
            for facility in FacilityType.objects.all()
        ]
        self.objects = facilities
        self.heading = "Facility Types"


def facility_icon_upload(request, facility_id):
    facility_type = get_object_or_404(FacilityType, pk=facility_id)
    form = forms.UploadImageForm(request.POST, request.FILES)
    if request.method == 'POST':
        if form.is_valid():
            try:
                storage.upload_facility_icon(facility_type, form.cleaned_data['image'])
                messages.success(request, 'Icon updated')
                return redirect('admin:edit_facility_type', facility_id)
            except storage.StorageException as e:
                messages.error(request, e)
    else:
        form = forms.UploadImageForm()

    return render(request, 'lists/facility_icon.html', {
        'form': form,
        'facility_type': facility_type,
    })


class ContactList(AdminListView):

    def initialize(self, request):
        self.partial = "partials/contact_table_contents.html"
        self.objects = ContactType.objects.all().order_by('name')
        self.heading = "Contact Types"


class OpeningList(AdminListView):

    def initialize(self, request):
        self.partial = "partials/opening_table_contents.html"
        self.objects = OpeningType.objects.all().order_by('name')
        self.heading = "Opening Types"

class EditType(View):

    form_class = None
    type = None
    type_model = None
    return_url = None
    rev_url= None
    update_msg = None
    partial = None
    template = "lists/edit_type_view.html"
    redirect_url = None
    heading = ""

    def initialize(self, request, id=None):
        pass

    def prepare(self, id=None):
        if id:
            self.type = get_object_or_404(self.type_model, id=id)
            self.return_url = reverse(self.rev_url, kwargs={'id': id})
        else:
            self.type = None
            self.return_url = reverse(self.rev_url)

    def get(self, request, *args, **kwargs):
        self.initialize(request)
        id = kwargs.get('id', None)
        self.prepare(id)
        form = self.form_class(instance=self.type)
        context = {
            'type': self.type,
            'form': form,
            'return_url': self.return_url,
            'heading': self.heading,
            'partial': self.partial,
        }
        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        self.initialize(request)
        id = kwargs.get('id', None)
        self.prepare(id)
        form = self.form_class(request.POST, instance=self.type)
        form.save()
        messages.success(request, self.update_msg)
        return redirect(self.redirect_url)


class EditFacilityType(EditType):

    def initialize(self, request):
        self.type_model = FacilityType
        self.rev_url = "admin:edit_facility_type"
        self.update_msg = "Facility type updated"
        self.form_class = forms.AdminFacilityTypeForm
        self.partial = "partials/facility_type_edit.html"
        self.redirect_url = 'admin:facility_types'
        self.heading = "Edit facility type"


class EditContactType(EditType):

    def initialize(self, request):
        self.type_model = ContactType
        self.rev_url = "admin:edit_contact_type"
        self.update_msg = "Contact type updated"
        self.form_class = forms.AdminContactTypeForm
        self.partial = "partials/contact_type_edit.html"
        self.redirect_url = 'admin:contact_types'
        self.heading = "Edit contact type"


class EditOpeningType(EditType):

    def initialize(self, request):
        self.type_model = OpeningType
        self.rev_url = "admin:edit_opening_type"
        self.update_msg = "Opening type updated"
        self.form_class = forms.AdminOpeningTypeForm
        self.partial = "partials/opening_type_edit.html"
        self.redirect_url = 'admin:opening_types'
        self.heading = "Edit opening type"


class DeleteType(View):
    redirect_url = None
    type_model = None
    delete_msg = ""

    def get(self, request):
        redirect(self.redirect_url)

    def post(self, request, *args, **kwargs):
        id = request.POST.get('id', None)
        if id:
            object = get_object_or_404(self.type_model, id=id)
            object.delete()
            messages.success(request, self.delete_msg)
        return redirect(self.redirect_url)


class DeleteFacilityType(DeleteType):

    redirect_url = 'admin:facility_types'
    type_model = FacilityType
    delete_msg = 'Facility type deleted'


class DeleteContactType(DeleteType):

    redirect_url = 'admin:contact_types'
    type_model = ContactType
    delete_msg = 'Contact type deleted'


class DeleteOpeningType(DeleteType):

    redirect_url = 'admin:opening_types'
    type_model = OpeningType
    delete_msg = 'Opening type deleted'