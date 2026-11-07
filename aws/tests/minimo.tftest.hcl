# Pruebas sin credenciales (proveedor simulado): verifican que el plan contiene sólo los recursos
# de la lista de gratuidad y los valores seguros por defecto.
mock_provider "aws" {
  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}" }
  }
}

variables {
  account_id   = "123456789012"
  budget_email = "pruebas@example.edu"
}

run "plan_minimo_seguro" {
  command = plan

  assert {
    condition     = module.storage.bucket_name == "uvcg-sgsi-lab-123456789012-us-east-1"
    error_message = "Nombre de bucket inesperado."
  }
  assert {
    condition     = var.object_expiration_days == 30
    error_message = "La expiración por defecto debe ser 30 días."
  }
}

run "region_no_permitida" {
  command = plan
  variables {
    region = "eu-west-1"
  }
  expect_failures = [var.region]
}
