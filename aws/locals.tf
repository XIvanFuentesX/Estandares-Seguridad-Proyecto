locals {
  tags = {
    Proyecto      = "SGSI-UVCG"
    Ambiente      = "academico-demo"
    Propietario   = "laboratorio-sgsi"
    Datos         = "ficticios"
    Costo         = "plan-free-cero-cargos"
    GestionadoPor = "terraform"
  }
  bucket_name = "${var.prefix}-${var.account_id}-${var.region}"
}
