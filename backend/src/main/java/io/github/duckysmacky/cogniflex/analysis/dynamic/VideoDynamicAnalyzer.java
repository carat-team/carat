package io.github.duckysmacky.cogniflex.analysis.dynamic;

import io.github.duckysmacky.cogniflex.analysis.ContentItem;
import io.github.duckysmacky.cogniflex.analysis.ContentType;
import io.github.duckysmacky.cogniflex.analysis.dynamic.inference.InferenceClient;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;

import java.util.concurrent.Executor;

@Component
public class VideoDynamicAnalyzer extends DynamicAnalyzer {
    private final InferenceClient mlClient;

    public VideoDynamicAnalyzer(
        InferenceClient mlClient,
        @Qualifier("dynamicAnalysisExecutor") Executor dynamicAnalysisExecutor
    ) {
        super(dynamicAnalysisExecutor);
        this.mlClient = mlClient;
    }

    @Override
    public boolean supports(ContentType type) {
        return type == ContentType.VIDEO;
    }

    @Override
    protected DynamicAnalysisResult analyzeDynamic(ContentItem item) {
        return mlClient.analyzeVideo(item.bytes());
    }
}
