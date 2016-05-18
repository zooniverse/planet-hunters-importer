group = PlanetHunterGroup.create({ name: 'kdwarf-1-synthetic' })

json = JSON.parse(File.read('/config/manifest.json')); nil

project = PlanetHunterSubject.project

workflow = PlanetHunterSubject.first.workflows.first

project_id = project.id
workflow_ids = [workflow.id]

total = json.length
json.each.with_index do |source, index|
  puts "#{ index + 1 } / #{ total }"

  coords = source["coords"]

  light_curves = source["light_curves"]
  metadata = source["metadata"]
  subject = PlanetHunterSubject.create({
    project_id: project_id,
    workflow_ids: workflow_ids,
    coords: coords,
    zooniverse_id: source["zooniverse_id"],
    location: { },
    group_id: group.id,
    metadata: metadata
  })

  light_curves.each do |light_curve|
    location = light_curve["location"]
    quarter = light_curve["quarter"]
    data_location = location
    subject.add_light_curve! quarter: quarter, data_location: data_location, start_time: light_curve['start_time']
  end
end; nil
