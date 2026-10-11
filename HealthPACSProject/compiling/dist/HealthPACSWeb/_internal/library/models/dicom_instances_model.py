# library/models/dicom_instances_model.py
from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from library.models.base_model import Base


class DicomInstancesModel(Base):
    """
    Mappatura ORM della tabella public.dicom_instances.
    Rappresenta la singola istanza DICOM (SOP Instance / file .dcm).
    """
    __tablename__ = "dicom_instances"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(
        Integer,
        ForeignKey("public.dicom_series.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sop_instance_uid = Column(String(128), nullable=False, unique=True, index=True)
    sop_class_uid = Column(String(128), nullable=True)
    instance_number = Column(Integer, nullable=True)
    transfer_syntax_uid = Column(String(128), nullable=True)
    file_path = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relazione ORM verso la serie padre (Usa il nome corretto della classe ORM)
    series = relationship("DicomSeriesModel", back_populates="instances")

    def to_dict(self):
        """Converte l'oggetto ORM in un dizionario Python."""
        return {
            "id": self.id,
            "series_id": self.series_id,
            "sop_instance_uid": self.sop_instance_uid,
            "sop_class_uid": self.sop_class_uid,
            "instance_number": self.instance_number,
            "transfer_syntax_uid": self.transfer_syntax_uid,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }