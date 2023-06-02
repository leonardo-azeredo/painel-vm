import tkinter as tk
from tkinter import ttk
from azure.identity import InteractiveBrowserCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient

# Azure authentication settings
subscription_id = '<SUBSCRIPTION-ID>'

# Create Azure resource management client
credential = InteractiveBrowserCredential()
resource_client = ResourceManagementClient(credential, subscription_id)

# Create Azure compute management client
compute_client = ComputeManagementClient(credential, subscription_id)

# Function to get the status of virtual machines in a resource group
def get_vm_status(resource_group_name, vm_name):
    vm = compute_client.virtual_machines.get(resource_group_name, vm_name, expand='instanceView')
    vm_status = vm.instance_view.statuses[1].display_status
    return vm_status

# Function to start or stop a virtual machine
def toggle_vm_power_state(resource_group_name, vm_name, button):
    vm_status = get_vm_status(resource_group_name, vm_name)

    if vm_status == 'VM running':
        # Shutdown the virtual machine
        compute_client.virtual_machines.begin_deallocate(resource_group_name, vm_name)
        button['text'] = f"{vm_name} (Shutdown)"
        button['bg'] = 'red'
    else:
        # Start the virtual machine
        compute_client.virtual_machines.begin_start(resource_group_name, vm_name)
        button['text'] = f"{vm_name} (Start)"
        button['bg'] = 'green'

# Create the window
window = tk.Tk()
window.title('Azure VM Control Panel')
window.configure(bg='gray')

# Create a frame for the buttons
frame = ttk.Frame(window)
frame.pack(fill='both', expand=True)

# Create a canvas with a scrollbar
canvas = tk.Canvas(frame)
scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side='left', fill='both', expand=True)
scrollbar.pack(side='right', fill='y')

# Get list of resource groups
resource_groups = list(resource_client.resource_groups.list())

# Create buttons for each virtual machine in each resource group
button_count = 0  # Track the number of buttons created
button_width = 30  # Button width
button_padding = 5  # Padding between buttons
window.update_idletasks()  # Update the window to get the correct width
window_width = window.winfo_width()  # Get the window width

for resource_group in resource_groups:
    resource_group_name = resource_group.name
    vms = compute_client.virtual_machines.list(resource_group_name)

    for vm in vms:
        vm_name = vm.name
        vm_status = get_vm_status(resource_group_name, vm_name)

        button_text = f"{vm_name} ({vm_status})"
        button = tk.Button(scrollable_frame, text=button_text, width=button_width, anchor='w')

        if vm_status == 'VM running':
            button['bg'] = 'green'
        elif vm_status == 'VM deallocated' or vm_status == 'VM stopped':
            button['bg'] = 'red'

        button['command'] = lambda r=resource_group_name, v=vm_name, b=button: toggle_vm_power_state(r, v, b)
        button.pack(padx=button_padding, pady=button_padding, fill='x')
        button_count += 1

# Configure uniform padding and stretching for all buttons
scrollable_frame.columnconfigure(0, weight=1)
for i in range(button_count):
    scrollable_frame.rowconfigure(i, weight=1)

# Update the canvas scrollregion to show all buttons
canvas.update_idletasks()
canvas.configure(scrollregion=canvas.bbox("all"))

# Resize the canvas to fit the window width
canvas.configure(width=window_width)

# Start the event loop
window.mainloop()
