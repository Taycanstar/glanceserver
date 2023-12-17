import csv
from django.conf import settings
import os
from glancenote.models import Student


def filter_csv_by_student(original_csv_path, student_id, key_column, output_csv_filename):
    output_csv_path = os.path.join(settings.MEDIA_ROOT, 'student_files', output_csv_filename)
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)

    with open(original_csv_path, mode='r') as infile, open(output_csv_path, mode='w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()

        for row in reader:
            if str(row[key_column]) == str(student_id):
                writer.writerow(row)

    return output_csv_path


def save_model_data_as_csv(model, filename):
    output_csv_path = os.path.join(settings.MEDIA_ROOT, 'model_data', filename)
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)

    with open(output_csv_path, mode='w', newline='') as outfile:
        writer = csv.writer(outfile)

        # Write header
        headers = [field.name for field in model._meta.fields]
        writer.writerow(headers)

        # Write data rows
        for instance in model.objects.all():
            writer.writerow([getattr(instance, field) for field in headers])

    return output_csv_path






