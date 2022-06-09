# %%
from m4i_analytics.m4i.platform.PlatformApi import PlatformApi

project_id = '<your project id>'

auth_options = {
    'username': '<your username>',
    'password': '<your password>'
}

# %%

# Get all exemptions for the sepecified project from the repository
exemptions = PlatformApi.get_metric_exemptions(project_id, **auth_options)

print([exemption.toDict() for exemption in exemptions])

if(len(exemptions) > 0):
    exemption = exemptions[0]

    # Delete the exemption from the repository
    PlatformApi.delete_metric_exemption(
        exemption.id, exemption.metric, exemption.project_id)

    # And recreate it
    exemption = PlatformApi.create_metric_exemption(exemption)

    print(exemption.toDict())
# END IF
