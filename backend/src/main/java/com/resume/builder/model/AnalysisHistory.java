package com.resume.builder.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Entity
@Table(name = "analysis_history")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AnalysisHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long resumeId;

    private String resumeName;

    private String type;

    private Integer score;

    @Lob
    @Column(columnDefinition = "CLOB")
    private String inputData;

    @Lob
    @Column(columnDefinition = "CLOB")
    private String resultData;

    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
